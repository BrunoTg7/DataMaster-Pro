"""
Realtime Sync - Sincronização em tempo real via WebSocket
Usa o cliente async do Supabase Realtime em uma thread dedicada.
Escuta mudanças nas tabelas `execucoes` e `scheduled_tasks`
e atualiza o SQLite local automaticamente.
"""
import threading
import asyncio
import json
import logging
from typing import Optional, Callable
from datetime import datetime

log = logging.getLogger(__name__)


class RealtimeSync:
    """Sincronização em tempo real via WebSocket com Supabase.

    Uso:
        sync = RealtimeSync(storage_manager)
        sync.start(access_token, user_id)

        # ... mais tarde ...
        sync.stop()
    """

    def __init__(self, storage_manager):
        self._storage = storage_manager
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._channel = None
        self._on_change: Optional[Callable] = None
        self._user_id: Optional[str] = None

    def set_on_change(self, callback: Callable):
        """Callback chamado quando dados mudam remotamente."""
        self._on_change = callback

    def start(self, access_token: str, user_id: str):
        """Inicia a escuta de mudanças em tempo real."""
        if self._running:
            log.warning("RealtimeSync já está rodando")
            return

        self._user_id = user_id
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, args=(access_token,),
            daemon=True, name="realtime-sync"
        )
        self._thread.start()
        log.info("RealtimeSync iniciado para user=%s", user_id[:8])

    def stop(self):
        """Para a escuta de mudanças."""
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._channel = None
        log.info("RealtimeSync parado")

    def _run_loop(self, access_token: str):
        """Executa o event loop asyncio em thread dedicada."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect(access_token))
        except Exception as e:
            log.error("RealtimeSync loop erro: %s", e)
        finally:
            self._loop.close()

    async def _connect(self, access_token: str):
        """Conecta ao Supabase Realtime e inscreve nos canais."""
        try:
            import config
            from realtime._async.client import AsyncRealtimeClient

            # Construir URL do WebSocket
            ws_url = config._u0.replace("https://", "wss://").replace("http://", "ws://")
            ws_url = ws_url.rstrip("/") + "/realtime/v1"

            client = AsyncRealtimeClient(
                ws_url,
                token=access_token,
                auto_reconnect=False,
                max_retries=2,
            )

            await client.connect()

            # Inscrever na tabela de execucoes
            channel = client.channel("datamaster:execucoes", {
                "config": {
                    "broadcast": {"self": False},
                    "presence": {"key": self._user_id},
                }
            })

            from realtime import RealtimePostgresChangesListenEvent

            channel.on_postgres_changes(
                event=RealtimePostgresChangesListenEvent.All,
                callback=self._on_execucoes_change,
                table="execucoes",
                schema="public",
                filter=f"usuario_id=eq.{self._user_id}",
            )

            channel.on_postgres_changes(
                event=RealtimePostgresChangesListenEvent.All,
                callback=self._on_scheduled_change,
                table="scheduled_tasks",
                schema="public",
                filter=f"user_id=eq.{self._user_id}",
            )

            await channel.subscribe()
            self._channel = channel
            log.info("RealtimeSync conectado e inscrito nos canais")

            # Manter vivo enquanto rodando
            while self._running:
                await asyncio.sleep(1)

            await client.close()

        except asyncio.CancelledError:
            log.info("RealtimeSync desconectado")
        except Exception as e:
            if self._running:
                log.warning("RealtimeSync indisponível (reconecta no próximo sync): %s", str(e)[:80])
            self._running = False

    def _on_execucoes_change(self, payload):
        """Callback para mudanças na tabela execucoes."""
        try:
            event_type = payload.event_type if hasattr(payload, 'event_type') else 'unknown'
            new_record = payload.new if hasattr(payload, 'new') else None
            old_record = payload.old if hasattr(payload, 'old') else None

            log.debug("Realtime execucoes: event=%s", event_type)

            # Sincronizar com SQLite local
            if self._user_id and new_record:
                self._sync_execution_to_local(new_record)

            if self._on_change:
                self._on_change("execucoes", event_type, new_record)

        except Exception as e:
            log.error("RealtimeSync erro ao processar mudança em execucoes: %s", e)

    def _on_scheduled_change(self, payload):
        """Callback para mudanças na tabela scheduled_tasks."""
        try:
            event_type = payload.event_type if hasattr(payload, 'event_type') else 'unknown'
            new_record = payload.new if hasattr(payload, 'new') else None

            log.debug("Realtime scheduled_tasks: event=%s", event_type)

            if self._user_id and new_record:
                self._sync_scheduled_to_local(new_record)

            if self._on_change:
                self._on_change("scheduled_tasks", event_type, new_record)

        except Exception as e:
            log.error("RealtimeSync erro ao processar mudança em scheduled_tasks: %s", e)

    def _sync_execution_to_local(self, record: dict):
        """Sincroniza uma execução remota para o SQLite local."""
        try:
            conn = self._storage._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO executions
                (user_id, tool_name, input_files, output_path, rows_processed,
                 hours_saved, status, duration_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get("usuario_id"),
                record.get("ferramenta"),
                json.dumps(record.get("input_files", [])),
                record.get("resultado_arquivo", ""),
                record.get("linhas_processadas", 0),
                record.get("tempo_economizado_minutos", 0) / 60,
                record.get("status", "completed"),
                record.get("tempo_execucao_ms", 0),
                record.get("created_at"),
            ))

            conn.commit()
            conn.close()
            log.debug("RealtimeSync: execução %s sincronizada localmente",
                      record.get("created_at", "")[:19])
        except Exception as e:
            log.error("RealtimeSync erro ao sincronizar execução: %s", e)

    def _sync_scheduled_to_local(self, record: dict):
        """Sincroniza uma tarefa agendada remota para o SQLite local."""
        try:
            conn = self._storage._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO scheduled_tasks_local
                (task_id, user_id, tool_name, tool_action, task_name,
                 input_files, schedule_frequency, cron_expression,
                 time_of_day, day_of_week, day_of_month, enabled,
                 last_run, next_run, execution_count, last_status,
                 last_error, config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get("task_id"),
                record.get("user_id"),
                record.get("tool_name"),
                record.get("tool_action"),
                record.get("task_name"),
                record.get("input_files", "[]"),
                record.get("schedule_frequency"),
                record.get("cron_expression"),
                record.get("time_of_day"),
                record.get("day_of_week"),
                record.get("day_of_month"),
                record.get("enabled", True),
                record.get("last_run"),
                record.get("next_run"),
                record.get("execution_count", 0),
                record.get("last_status"),
                record.get("last_error"),
                record.get("config"),
            ))

            conn.commit()
            conn.close()
            log.debug("RealtimeSync: tarefa agendada %s sincronizada",
                      record.get("task_id", "")[:8])
        except Exception as e:
            log.error("RealtimeSync erro ao sincronizar tarefa agendada: %s", e)

    @property
    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()


# ── Singleton ────────────────────────────────────────────────────────────────

_instance: Optional[RealtimeSync] = None
_instance_lock = threading.Lock()


def get_realtime_sync(storage_manager=None) -> RealtimeSync:
    """Obtém a instância singleton do RealtimeSync."""
    global _instance
    with _instance_lock:
        if _instance is None:
            if storage_manager is None:
                from src.core.storage.storage_manager import StorageManager
                storage_manager = StorageManager()
            _instance = RealtimeSync(storage_manager)
        return _instance
