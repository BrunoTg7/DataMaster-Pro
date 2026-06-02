"""
Sync Manager - Offline synchronization queue and Execution Tracking
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading
import time
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

from src.core.circuit_breaker import get_circuit_breaker, CircuitBreakerError
from src.core.feature_flags import is_feature_enabled
from src.core.apm import PerformanceMonitor
from src.utils.network import retry, RateLimiter

log = logging.getLogger(__name__)

# Rate limiter para chamadas Supabase
_supabase_limiter = RateLimiter(max_calls=30, period=60)


class SyncManager:
    def __init__(self, storage_manager, on_sync_complete=None):
        self.storage = storage_manager
        self._init_queue_table()
        self.is_syncing = False
        self._sync_lock = threading.Lock()
        self.last_sync = None
        self._on_sync_complete = on_sync_complete
        self._c = None
        self._ct = None

    def _get_client(self, access_token: str = None):
        """Retorna cliente cacheado, recria se token mudar"""
        from supabase import create_client
        if self._c is None or (access_token and access_token != self._ct):
            self._c = create_client(
                config._u0, config._r1()
            )
            self._ct = access_token
            if access_token:
                self._c.postgrest.auth(access_token)
        return self._c

    def set_on_sync_complete(self, callback):
        self._on_sync_complete = callback

    def _get_conn(self):
        """Retorna conexão SQLite com WAL + busy_timeout para evitar database is locked"""
        conn = sqlite3.connect(config.DB_PATH, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_queue_table(self):
        """Cria tabela de fila de sincronização"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                table_name TEXT NOT NULL,
                data_json TEXT NOT NULL,
                usuario_id TEXT,
                data_execucao TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP NULL,
                retry_count INTEGER DEFAULT 0
            )
        """)
        
        # Migração: Adicionar colunas se não existirem
        try:
            cursor.execute("SELECT usuario_id FROM sync_queue LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE sync_queue ADD COLUMN usuario_id TEXT")
            cursor.execute("ALTER TABLE sync_queue ADD COLUMN data_execucao TIMESTAMP")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add_to_queue(self, operation: str, table_name: str, data: Dict) -> int:
        """
        Adiciona operação à fila de sincronização com metadados explícitos
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        usuario_id = data.get("usuario_id") or data.get("user_id")
        data_exec = data.get("created_at") or datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO sync_queue (operation, table_name, data_json, usuario_id, data_execucao, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (operation, table_name, json.dumps(data), usuario_id, data_exec))

        queue_id = cursor.lastrowid
        conn.commit()
        conn.close()

        log.info(f"Added to sync queue: ID={queue_id}, user={usuario_id}")
        return queue_id

    def get_pending_items(self, limit: int = 50) -> List[Dict]:
        """Retorna itens pendentes na fila"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, operation, table_name, data_json, status, created_at, retry_count
            FROM sync_queue
            WHERE status IN ('pending', 'failed') AND retry_count < 3
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "operation": row[1],
                "table_name": row[2],
                "data": json.loads(row[3]),
                "status": row[4],
                "created_at": row[5],
                "retry_count": row[6]
            }
            for row in rows
        ]

    def mark_synced(self, queue_id: int):
        """Marca item como sincronizado"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sync_queue
            SET status = 'synced', synced_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), queue_id))

        conn.commit()
        conn.close()

    def mark_failed(self, queue_id: int):
        """Marca item como falhou e incrementa retry"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sync_queue
            SET status = 'failed', retry_count = retry_count + 1
            WHERE id = ?
        """, (queue_id,))

        conn.commit()
        conn.close()

    def get_queue_stats(self) -> Dict:
        """Retorna estatísticas da fila"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM sync_queue
            GROUP BY status
        """)

        rows = cursor.fetchall()
        conn.close()

        stats = {"pending": 0, "synced": 0, "failed": 0}
        for row in rows:
            stats[row[0]] = row[1]

        return stats

    def check_connection(self) -> bool:
        """Verifica se há conexão com a internet"""
        from src.utils.network import check_internet_connection
        return check_internet_connection()

    def _authenticate(self, client, access_token: str) -> bool:
        """Autentica client com token ou re-login com credenciais salvas."""
        if access_token:
            try:
                client.postgrest.auth(access_token)
                client.auth.get_user()
                log.debug("Token existente ainda válido")
                return True
            except Exception:
                log.warning("Token expirado, tentando re-login com credenciais salvas...")

        # Tenta re-login com credenciais (refresh token) salvas
        for tentativa in range(2):
            try:
                creds = self.storage.get_stored_credentials()
                if creds and creds.get("refresh_token"):
                    login = client.auth.refresh_session(creds["refresh_token"])
                    if login and login.user:
                        new_token = login.session.access_token
                        new_refresh = login.session.refresh_token
                        client.postgrest.auth(new_token)
                        # Atualiza o token salvo localmente
                        user_data = self.storage.get_saved_session()
                        if user_data:
                            user_data["session_token"] = new_token
                            user_data["refresh_token"] = new_refresh
                            user_data["expires_at"] = (datetime.now() + timedelta(days=90)).isoformat()
                            self.storage.save_user_session(user_data)
                        log.info("Re-login automático realizado com sucesso via refresh_token")
                        return True
                else:
                    log.error("Nenhum refresh_token salvo encontrado para re-login")
                    return False
            except Exception as e:
                error_msg = str(e)
                # Refresh token inválido — limpar sessão local e não tentar novamente
                if "Refresh Token Not Found" in error_msg or "Invalid Refresh Token" in error_msg:
                    log.warning("Refresh token inválido/expirado, limpando sessão local")
                    self.storage.clear_session()
                    return False
                log.error(f"Re-login automático falhou (tentativa {tentativa+1}): {e}")
                if tentativa == 0:
                    time.sleep(1)
        return False

    def sync_now(self) -> Dict:
        """
        Executa sincronização imediata (upload + download)
        """
        apm = PerformanceMonitor.get_instance()
        sync_span = apm.start("sync_now")

        with self._sync_lock:
            if self.is_syncing:
                log.warning("sync_now ignorado: já está em andamento")
                apm.end(sync_span, "skipped")
                return {"success": False, "error": "Em andamento"}
            if not self.check_connection():
                log.warning("sync_now ignorado: sem conexão")
                apm.end(sync_span, "no_connection")
                return {"success": False, "error": "Sem conexão", "offline": True}

            now = time.time()
            if getattr(self, '_last_sync_time', 0) > now - 10:
                log.warning("sync_now ignorado: cooldown de 10s")
                return {"success": False, "error": "Cooldown de 10s entre sincronizações"}
            self._last_sync_time = now

            self.is_syncing = True

        results = {"synced": 0, "failed": 0}

        # Circuit breaker para proteger contra falhas do Supabase
        cb = get_circuit_breaker("supabase", failure_threshold=5, recovery_timeout=60)

        try:
            access_token = self.storage.get_token()
            log.debug(f"sync_now: token obtido: {'sim' if access_token else 'não'}")
            _c = self._get_client(access_token)

            if not self._authenticate(_c, access_token):
                log.error("Falha na autenticação — sync abortado")
                return {"success": False, "error": "Falha na autenticação"}

            # ── 1. UPLOAD ─────────────────────────────────────────────
            upload_span = apm.start("sync_upload")
            pending = self.get_pending_items()
            log.info(f"sync_now: {len(pending)} itens pendentes na fila")
            if pending:
                for item in pending:
                    try:
                        data = item["data"]
                        log.debug(f"sync_now: enviando item {item['id']}: ferramenta={data.get('ferramenta') or data.get('tool_name')}")
                        mapped_data = {
                            "usuario_id": data.get("usuario_id") or data.get("user_id"),
                            "ferramenta": data.get("ferramenta") or data.get("tool_name"),
                            "linhas_processadas": int(data.get("linhas_processadas") or 0),
                            "tempo_execucao_ms": int(data.get("tempo_execucao_ms") or 0),
                            "tempo_economizado_minutos": int(data.get("tempo_economizado_minutos") or 0),
                            "resultado_arquivo": data.get("resultado_arquivo"),
                            "created_at": data.get("created_at")
                        }

                        cb.call(
                            lambda: _c.table("execucoes").upsert(mapped_data, on_conflict="usuario_id,created_at").execute()
                        )
                        self.mark_synced(item["id"])
                        results["synced"] += 1
                        log.info(f"sync_now: item {item['id']} sincronizado com sucesso")
                    except Exception as e:
                        log.error(f"sync_now: erro ao sincronizar item {item['id']}: {e}")
                        self.mark_failed(item["id"])
                        results["failed"] += 1
            apm.end(upload_span, "ok" if results["failed"] == 0 else "partial")

            if results["synced"] > 0:
                user_data = self.storage.get_user_data()
                user_id = user_data.get("id") if user_data else None
                if user_id:
                    import requests
                    requests.post(f"{config._u0}/functions/v1/sync-background",
                                 headers={"Authorization": f"Bearer {config._r1()}"},
                                 json={"usuario_id": user_id}, timeout=5)

            # ── 2. DOWNLOAD do Supabase para SQLite local ─────────────
            download_span = apm.start("sync_download")
            user_data = self.storage.get_user_data()
            if user_data and user_data.get("id"):
                try:
                    remote = cb.call(
                        lambda: _c.table("execucoes").select("*").eq("usuario_id", user_data["id"]).order("created_at", desc=True).limit(2000).execute()
                    )
                    remote_records = remote.data or []
                    self.storage.replace_user_executions(user_data["id"], remote_records)
                    log.info(f"Sync download: {len(remote_records)} registros de execuções espelhados")
                except CircuitBreakerError:
                    log.warning("Sync download bloqueado pelo circuit breaker")
                except Exception as e:
                    log.error(f"Sync download erro: {e}")
            apm.end(download_span, "ok")

            # ── 3. SCHEDULED TASKS sync (upload + download) ──────────
            scheduled_span = apm.start("sync_scheduled_tasks")
            try:
                self._upload_scheduled_tasks(_c, cb)
                self._download_scheduled_tasks(_c, cb)
            except CircuitBreakerError:
                log.warning("Scheduled tasks sync bloqueado pelo circuit breaker")
            apm.end(scheduled_span, "ok")

            # ── 4. LIMPEZA da fila de sync ────────────────────────────
            self._cleanup_queue()

            with self._sync_lock:
                if self._on_sync_complete:
                    self._on_sync_complete()

        finally:
            with self._sync_lock:
                self.is_syncing = False

        apm.end(sync_span, "ok" if results["failed"] == 0 else "partial")
        return {"success": results["failed"] == 0, "synced": results["synced"]}

    def _cleanup_queue(self):
        """Remove itens sincronizados e falhas permanentes da fila"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sync_queue WHERE status = 'synced'")
        cursor.execute("DELETE FROM sync_queue WHERE status = 'failed' AND retry_count >= 3")
        removed = cursor.rowcount
        conn.commit()
        conn.close()
        if removed > 0:
            log.info(f"Limpou {removed} itens da fila de sync")

    def _upload_scheduled_tasks(self, client, cb=None) -> int:
        """Envia tarefas agendadas locais para o servidor"""
        user_data = self.storage.get_user_data()
        if not user_data or not user_data.get("id"):
            return 0

        local_tasks = self.storage.get_all_scheduled_tasks(user_data["id"])
        synced = 0

        for task in local_tasks:
            try:
                upsert_fn = lambda t=task: client.table("scheduled_tasks").upsert({
                    "task_id": t["task_id"],
                    "user_id": t["user_id"],
                    "tool_name": t["tool_name"],
                    "tool_action": t["tool_action"],
                    "task_name": t.get("task_name"),
                    "input_files": json.dumps(t.get("input_files", [])),
                    "schedule_frequency": t["schedule_frequency"],
                    "cron_expression": t.get("cron_expression"),
                    "time_of_day": t.get("time_of_day"),
                    "day_of_week": t.get("day_of_week"),
                    "day_of_month": t.get("day_of_month"),
                    "enabled": t.get("enabled", True),
                    "last_run": t.get("last_run"),
                    "next_run": t.get("next_run"),
                    "execution_count": t.get("execution_count", 0),
                    "last_status": t.get("last_status"),
                    "last_error": t.get("last_error"),
                    "config": json.dumps(t.get("config")) if t.get("config") else None,
                }, on_conflict="task_id").execute()

                if cb:
                    cb.call(upsert_fn)
                else:
                    upsert_fn()
                synced += 1
            except Exception as e:
                log.error(f"Erro ao sincronizar tarefa {task['task_id']}: {e}")

        if synced:
            log.info(f"Scheduled tasks upload: {synced} tarefas sincronizadas")
        return synced

    def _download_scheduled_tasks(self, client, cb=None):
        """Baixa tarefas agendadas do servidor para o SQLite local"""
        user_data = self.storage.get_user_data()
        if not user_data or not user_data.get("id"):
            return

        try:
            download_fn = lambda: (
                client.table("scheduled_tasks")
                .select("*")
                .eq("user_id", user_data["id"])
                .execute()
            )

            if cb:
                remote = cb.call(download_fn)
            else:
                remote = download_fn()

            remote_tasks = remote.data or []
            if remote_tasks:
                self.storage.replace_scheduled_tasks_for_user(user_data["id"], remote_tasks)
                log.info(f"Scheduled tasks download: {len(remote_tasks)} registros espelhados")
        except CircuitBreakerError:
            log.warning("Scheduled tasks download bloqueado pelo circuit breaker")
        except Exception as e:
            log.error(f"Erro ao baixar scheduled_tasks: {e}")

    def sync_theme(self, theme: str):
        """Sincroniza o tema selecionado com o servidor"""
        try:
            user_data = self.storage.get_user_data()
            if not user_data or not user_data.get("id"):
                return
            
            access_token = self.storage.get_token()
            from supabase import create_client
            _c = create_client(config._u0, config._r1())
            if access_token: 
                _c.postgrest.auth(access_token)
            
            _c.table("usuarios").update({
                "preferencias_tema": theme,
                "updated_at": datetime.now().isoformat()
            }).eq("id", user_data["id"]).execute()
            
            log.info(f"Tema '{theme}' sincronizado")
        except Exception as e:
            log.error(f"Erro ao sincronizar tema: {e}")


class ExecutionTracker:
    """Rastreador de execuções com foco em Limites Dinâmicos"""

    def __init__(self, storage_manager, sync_manager: SyncManager):
        self.storage = storage_manager
        self.sync = sync_manager
        from src.core.memory_cache import get_cache
        self._cache = get_cache()
        self.sync.set_on_sync_complete(self._on_sync_done)

    def _on_sync_done(self):
        self.invalidate_stats_cache()

    def invalidate_stats_cache(self):
        self._cache.clear(prefix="user_stats:")
        log.debug("Stats cache invalidated after sync")

    def track_execution(self, tool_name: str, user_id: str, input_files: List[str],
                        output_path: str, status: str = "completed", duration_ms: int = 0,
                        rows_processed: int = 0, hours_saved: float = 0):
        """
        Registra uma execução e agenda sincronização
        """
        apm = PerformanceMonitor.get_instance()
        span = apm.start("track_execution", {"tool": tool_name})
        execution_data = {
            "usuario_id": user_id,
            "ferramenta": tool_name,
            "linhas_processadas": rows_processed,
            "tempo_execucao_ms": duration_ms,
            "tempo_economizado_minutos": int(hours_saved * 60),
            "resultado_arquivo": output_path,
            "created_at": datetime.now().isoformat()
        }

        # Salva local
        self.storage.save_execution(user_id, tool_name, input_files, output_path, rows_processed, hours_saved)

        # Envia para a fila de sync
        self.sync.add_to_queue("insert", "execucoes", execution_data)

        # Sincronização imediata se houver internet
        threading.Thread(target=self.sync.sync_now, daemon=True).start()

        # Notificação desktop
        self._notify_user(tool_name, rows_processed, hours_saved)

        self.invalidate_stats_cache()
        apm.end(span, "ok")
        return execution_data

    def _notify_user(self, tool_name: str, rows: int, hours: float):
        user_data = self.storage.get_saved_session()
        if not user_data or not user_data.get("notificacoes_desktop", True):
            return
        
        from src.utils.notifications import notification_manager
        notification_manager.send_async(
            title=f"✅ {tool_name.capitalize()} Concluído!",
            message=f"Processadas {rows} linhas.\nTempo economizado: {hours:.1f}h."
        )

    def get_current_cycle_start(self, user_created_at: str) -> datetime:
        """Calcula início do ciclo"""
        if not user_created_at: return datetime.now() - timedelta(days=30)
        try: created_dt = datetime.fromisoformat(user_created_at.replace('Z', '+00:00'))
        except Exception: return datetime.now() - timedelta(days=30)
        
        now = datetime.now(created_dt.tzinfo)
        try: current = now.replace(day=created_dt.day, hour=0, minute=0, second=0, microsecond=0)
        except Exception:
            import calendar
            current = now.replace(day=calendar.monthrange(now.year, now.month)[1], hour=0, minute=0, second=0)
            
        if current > now:
            month, year = (now.month - 1, now.year) if now.month > 1 else (12, now.year - 1)
            try: current = current.replace(year=year, month=month, day=created_dt.day)
            except Exception:
                import calendar
                current = current.replace(year=year, month=month, day=calendar.monthrange(year, month)[1])
        return current

    def get_user_stats(self, user_id: str, start_date: datetime = None) -> Dict:
        """Busca estatísticas - Prioridade Supabase (Online)"""
        cache_key = f"user_stats:{user_id}_{start_date.isoformat() if start_date else 'none'}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = None

        if self.sync.check_connection():
            try:
                token = self.storage.get_token()
                _c = self.sync._get_client(token)

                start_iso = start_date.isoformat() if start_date else (datetime.now() - timedelta(days=30)).isoformat()
                res = _c.table("execucoes").select("*").eq("usuario_id", user_id).gte("created_at", start_iso).execute()

                if res.data:
                    stats_by_tool = {}
                    total_lines = 0
                    total_hours = 0
                    for ex in res.data:
                        tool = ex.get("ferramenta", "unknown")
                        if tool not in stats_by_tool: stats_by_tool[tool] = {"execs": 0, "lines": 0}
                        stats_by_tool[tool]["execs"] += 1
                        stats_by_tool[tool]["lines"] += ex.get("linhas_processadas", 0)
                        total_lines += ex.get("linhas_processadas", 0)
                        total_hours += (ex.get("tempo_economizado_minutos", 0) / 60)

                    result = {
                        "total_lines": total_lines,
                        "total_hours": total_hours,
                        "total_executions": len(res.data),
                        "by_tool": stats_by_tool
                    }
            except Exception as e:
                log.error(f"Erro ao buscar stats online: {e}")

        if result is None:
            executions = self.storage.get_executions(user_id, limit=2000)
            total_lines = total_hours = total_execs = 0
            stats_by_tool = {}
            for ex in executions:
                try:
                    ex_date = datetime.fromisoformat(ex["created_at"])
                    if start_date and ex_date.timestamp() < start_date.timestamp(): continue

                    tool = ex.get("tool_name", "unknown")
                    if tool not in stats_by_tool: stats_by_tool[tool] = {"execs": 0, "lines": 0}
                    stats_by_tool[tool]["execs"] += 1
                    stats_by_tool[tool]["lines"] += ex.get("rows_processed", 0)

                    total_lines += ex.get("rows_processed", 0)
                    total_hours += ex.get("hours_saved", 0)
                    total_execs += 1
                except Exception:
                    pass
            result = {
                "total_lines": total_lines,
                "total_hours": total_hours,
                "total_executions": total_execs,
                "by_tool": stats_by_tool
            }

        if result and result.get("by_tool"):
            for tool_key in list(result["by_tool"].keys()):
                result["by_tool"][tool_key]["lines"] = result["by_tool"][tool_key].get("lines", 0)
                result["by_tool"][tool_key]["execs"] = result["by_tool"][tool_key].get("execs", 0)

        if result:
            self._cache.set(cache_key, result, ttl=30)
        return result

    def _is_plan_expired(self, user_data: Dict) -> bool:
        """Verifica se o plano PRO/Enterprise está expirado pela data_expiracao"""
        plan = (user_data or {}).get("plan", "gratis")
        if plan == "gratis":
            return False

        data_expiracao = (user_data or {}).get("data_expiracao")
        if not data_expiracao:
            return False

        try:
            exp_date = datetime.fromisoformat(data_expiracao.replace("Z", "+00:00").replace(" ", "T"))
            agora = datetime.now(exp_date.tzinfo) if exp_date.tzinfo else datetime.now()
            return exp_date <= agora
        except Exception:
            return False

    def check_limit(self, user_id: str, plan_name: str, tool_key: str = None, rows_to_process: int = 0) -> Dict:
        """
        Verificação inteligente de limites por ferramenta
        """
        user_data = self.storage.get_saved_session()
        created_at = user_data.get("created_at") if user_data else None
        cycle_start = self.get_current_cycle_start(created_at)
        
        stats = self.get_user_stats(user_id, start_date=cycle_start)
        
        plan_type = config.PlanType[plan_name.upper()] if plan_name.upper() in config.PlanType.__members__ else config.PlanType.GRATIS
        plan_info = config.PLAN_LIMITS.get(plan_type)

        # Verificar expiração do plano
        if self._is_plan_expired(user_data):
            return {
                "allowed": False,
                "error": "Seu plano PRO expirou. Renove sua assinatura para continuar usando todos os recursos.\n\nAcesse: https://data-master-pro.vercel.app/planos"
            }

        # Se for PRO ou Enterprise e não expirado, liberado
        if plan_type != config.PlanType.GRATIS:
            return {"allowed": True, "max": None}

        # 1. Verificar Limite Global de Linhas
        max_global_lines = plan_info.get("max_lines_month", 1200)
        current_total_lines = stats.get("total_lines", 0)
        
        if current_total_lines >= max_global_lines:
            return {
                "allowed": False,
                "error": f"Limite global de {max_global_lines} linhas atingido.\nAssine o PRO!",
                "max_lines": max_global_lines
            }

        # 2. Verificar Limite Global de Execuções
        max_global_execs = plan_info.get("max_execs_month", 15)
        current_total_execs = stats.get("total_executions", 0)

        if current_total_execs >= max_global_execs:
            return {
                "allowed": False,
                "error": f"Você atingiu o limite de {max_global_execs} tarefas mensais.\nAssine o PRO!",
                "max_execs": max_global_execs
            }

        # 2. Verificar Limite Específico da Ferramenta (se fornecida)
        if tool_key:
            tool_limits = plan_info.get("tools_limit", {})
            limit = tool_limits.get(tool_key)

            if limit:
                max_total = limit.get("max_per_exec")  # Limite total (ex: 15 documentos ou 600 linhas)
                max_execs = limit.get("max_execs")  # Limite de execuções
                
                current_tool_stats = stats.get("by_tool", {}).get(tool_key, {"execs": 0, "lines": 0})
                current_execs = current_tool_stats.get("execs", 0)
                current_lines = current_tool_stats.get("lines", 0)

                # 1. Verificar Limite de Execuções Totais
                if max_execs and current_execs >= max_execs:
                    unit = "documentos" if tool_key == "orcamentos" else "linhas"
                    return {
                        "allowed": False,
                        "error": f"Você já atingiu o limite de {max_execs} execuções desta ferramenta este mês."
                    }

                # 2. Verificar Limite Total Acumulado (ex: 15 documentos ou 600 linhas no total do mês)
                if max_total and current_lines + rows_to_process > max_total:
                    unit = "documentos" if tool_key == "orcamentos" else "linhas"
                    return {
                        "allowed": False,
                        "error": f"Você atingiu o limite total de {max_total} {unit} mensais desta ferramenta.\nAssine o PRO para continuar!"
                    }
            
        return {"allowed": True, "current": current_total_lines, "max": max_global_lines}