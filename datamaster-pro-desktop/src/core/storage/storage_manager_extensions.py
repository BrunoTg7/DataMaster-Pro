"""
Storage Manager Extensions - Métodos para as 3 novas tabelas de planos
(execution_logs, scheduled_tasks, tool_configurations)

Este arquivo contém extensões para o StorageManager que suportam:
- Logs locais de execução (SQLite) + sync com Supabase (cloud)
- Tarefas agendadas (SQLite local)
- Configurações de ferramentas (SQLite local)
"""
import sqlite3
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class StorageManagerExtensions:
    """
    Extensões para StorageManager para as novas tabelas de planos.
    Adicione estes métodos à classe StorageManager existente.
    """

    # ========================================================================
    # EXECUTION_LOGS - Logs de execução com ROI (Local)
    # ========================================================================

    def _init_execution_logs_table(self):
        """Inicializa tabela execution_logs no SQLite local"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_logs_local (
                    execution_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    lines_processed INTEGER DEFAULT 0,
                    file_size_bytes INTEGER DEFAULT 0,
                    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'cancelled')),
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_exec_logs_user_tool 
                ON execution_logs_local(user_id, tool_name, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_exec_logs_timestamp 
                ON execution_logs_local(timestamp DESC)
            """)
            
            conn.commit()
            conn.close()
            logger.info("Tabela execution_logs_local inicializada")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar execution_logs_local: {e}")

    def save_execution_log(self, execution_log) -> bool:
        """
        Salva log de execução no SQLite local
        
        Args:
            execution_log: ExecutionLog object from roi_logger.py
            
        Returns:
            True se salvo com sucesso
        """
        try:
            self._init_execution_logs_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO execution_logs_local (
                    execution_id, user_id, tool_name, timestamp, 
                    duration_seconds, lines_processed, file_size_bytes, 
                    status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_log.execution_id,
                execution_log.user_id,
                execution_log.tool_name,
                execution_log.timestamp,
                execution_log.duration_seconds,
                execution_log.lines_processed,
                execution_log.file_size_bytes,
                execution_log.status,
                execution_log.error_message
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Log de execução salvo: {execution_log.execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar log de execução: {e}")
            return False

    def get_execution_logs(self, user_id: str, days: int = 7) -> List:
        """
        Recupera logs de execução do SQLite local
        
        Args:
            user_id: ID do usuário
            days: Últimos N dias
            
        Returns:
            Lista de dicts com logs
        """
        try:
            self._init_execution_logs_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Calcular data limite
            from datetime import datetime, timedelta
            limit_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                SELECT execution_id, user_id, tool_name, timestamp, 
                       duration_seconds, lines_processed, file_size_bytes, 
                       status, error_message
                FROM execution_logs_local
                WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (user_id, limit_date))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "execution_id": row[0],
                    "user_id": row[1],
                    "tool_name": row[2],
                    "timestamp": row[3],
                    "duration_seconds": row[4],
                    "lines_processed": row[5],
                    "file_size_bytes": row[6],
                    "status": row[7],
                    "error_message": row[8]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao recuperar logs de execução: {e}")
            return []

    # ========================================================================
    # SCHEDULED_TASKS - Tarefas agendadas (Local)
    # ========================================================================

    def _init_scheduled_tasks_table(self):
        """Inicializa tabela scheduled_tasks no SQLite local"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks_local (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_action TEXT NOT NULL,
                    task_name TEXT,
                    input_files TEXT NOT NULL,
                    schedule_frequency TEXT NOT NULL,
                    cron_expression TEXT,
                    time_of_day TEXT,
                    day_of_week INTEGER,
                    day_of_month INTEGER,
                    enabled BOOLEAN DEFAULT 1,
                    last_run TEXT,
                    next_run TEXT NOT NULL,
                    execution_count INTEGER DEFAULT 0,
                    last_status TEXT,
                    last_error TEXT,
                    config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sched_tasks_user 
                ON scheduled_tasks_local(user_id, enabled, next_run)
            """)
            
            conn.commit()
            conn.close()
            logger.info("Tabela scheduled_tasks_local inicializada")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar scheduled_tasks_local: {e}")

    def save_scheduled_task(self, task) -> bool:
        """Salva tarefa agendada no SQLite local"""
        try:
            self._init_scheduled_tasks_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO scheduled_tasks_local (
                    task_id, user_id, tool_name, tool_action, task_name,
                    input_files, schedule_frequency, cron_expression,
                    time_of_day, day_of_week, day_of_month, enabled,
                    last_run, next_run, execution_count, last_status,
                    last_error, config
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id, task.user_id, task.tool_name, task.tool_action,
                task.task_name, json.dumps(task.input_files),
                task.schedule_frequency, task.cron_expression,
                task.time_of_day, task.day_of_week, task.day_of_month,
                task.enabled, task.last_run, task.next_run,
                task.execution_count, task.last_status, task.last_error,
                json.dumps(task.config) if task.config else None
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Tarefa agendada salva: {task.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar tarefa agendada: {e}")
            return False

    def get_scheduled_tasks(self, user_id: str) -> List:
        """Recupera tarefas agendadas do usuário"""
        try:
            self._init_scheduled_tasks_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT task_id, user_id, tool_name, tool_action, task_name,
                       input_files, schedule_frequency, cron_expression,
                       time_of_day, day_of_week, day_of_month, enabled,
                       last_run, next_run, execution_count, last_status,
                       last_error, config
                FROM scheduled_tasks_local
                WHERE user_id = ?
                ORDER BY next_run ASC
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "task_id": row[0],
                    "user_id": row[1],
                    "tool_name": row[2],
                    "tool_action": row[3],
                    "task_name": row[4],
                    "input_files": json.loads(row[5]) if row[5] else [],
                    "schedule_frequency": row[6],
                    "cron_expression": row[7],
                    "time_of_day": row[8],
                    "day_of_week": row[9],
                    "day_of_month": row[10],
                    "enabled": bool(row[11]),
                    "last_run": row[12],
                    "next_run": row[13],
                    "execution_count": row[14],
                    "last_status": row[15],
                    "last_error": row[16],
                    "config": json.loads(row[17]) if row[17] else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao recuperar tarefas agendadas: {e}")
            return []

    def update_scheduled_task(self, task) -> bool:
        """Atualiza tarefa agendada"""
        try:
            self._init_scheduled_tasks_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scheduled_tasks_local SET
                    last_run = ?, next_run = ?, execution_count = ?,
                    last_status = ?, last_error = ?, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
            """, (
                task.last_run, task.next_run, task.execution_count,
                task.last_status, task.last_error, task.task_id
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar tarefa: {e}")
            return False

    def disable_scheduled_task(self, task_id: str) -> bool:
        """Desabilita uma tarefa agendada"""
        try:
            self._init_scheduled_tasks_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scheduled_tasks_local SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
            """, (task_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao desabilitar tarefa: {e}")
            return False

    def delete_scheduled_task(self, task_id: str) -> bool:
        """Deleta uma tarefa agendada"""
        try:
            self._init_scheduled_tasks_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM scheduled_tasks_local WHERE task_id = ?", (task_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar tarefa: {e}")
            return False

    # ========================================================================
    # TOOL_CONFIGURATIONS - Configurações de ferramentas (Local)
    # ========================================================================

    def _init_tool_configurations_table(self):
        """Inicializa tabela tool_configurations no SQLite local"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_configurations_local (
                    config_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tool_id TEXT NOT NULL,
                    config_name TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    description TEXT,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, tool_id, config_name)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_config_user_tool 
                ON tool_configurations_local(user_id, tool_id)
            """)
            
            conn.commit()
            conn.close()
            logger.info("Tabela tool_configurations_local inicializada")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar tool_configurations_local: {e}")

    def save_tool_configuration(self, config) -> bool:
        """Salva configuração de ferramenta"""
        try:
            self._init_tool_configurations_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO tool_configurations_local (
                    config_id, user_id, tool_id, config_name, config_data,
                    description, is_default
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                config.get("config_id"),
                config.get("user_id"),
                config.get("tool_id"),
                config.get("config_name"),
                json.dumps(config.get("config_data", {})),
                config.get("description"),
                config.get("is_default", False)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Configuração salva: {config.get('config_name')}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            return False

    def get_tool_configurations(self, user_id: str, tool_id: str) -> List:
        """Recupera configurações de uma ferramenta"""
        try:
            self._init_tool_configurations_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT config_id, config_name, config_data, is_default, description
                FROM tool_configurations_local
                WHERE user_id = ? AND tool_id = ?
                ORDER BY is_default DESC, config_name ASC
            """, (user_id, tool_id))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "config_id": row[0],
                    "config_name": row[1],
                    "config_data": json.loads(row[2]) if row[2] else {},
                    "is_default": bool(row[3]),
                    "description": row[4]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao recuperar configurações: {e}")
            return []

    def get_default_configuration(self, user_id: str, tool_id: str) -> Optional[Dict]:
        """Recupera configuração padrão de uma ferramenta"""
        try:
            self._init_tool_configurations_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT config_id, config_name, config_data, description
                FROM tool_configurations_local
                WHERE user_id = ? AND tool_id = ? AND is_default = 1
                LIMIT 1
            """, (user_id, tool_id))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "config_id": row[0],
                    "config_name": row[1],
                    "config_data": json.loads(row[2]) if row[2] else {},
                    "description": row[3]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar configuração padrão: {e}")
            return None

    def delete_tool_configuration(self, config_id: str) -> bool:
        """Deleta uma configuração de ferramenta"""
        try:
            self._init_tool_configurations_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM tool_configurations_local WHERE config_id = ?", (config_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar configuração: {e}")
            return False

    def set_default_configuration(self, user_id: str, tool_id: str, config_id: str) -> bool:
        """Define uma configuração como padrão"""
        try:
            self._init_tool_configurations_table()
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Primeiro, remover default de todas
            cursor.execute("""
                UPDATE tool_configurations_local SET is_default = 0
                WHERE user_id = ? AND tool_id = ?
            """, (user_id, tool_id))
            
            # Depois, setar a selecionada como default
            cursor.execute("""
                UPDATE tool_configurations_local SET is_default = 1
                WHERE config_id = ?
            """, (config_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao setar configuração padrão: {e}")
            return False


# ============================================================================
# INSTRUÇÕES DE INTEGRAÇÃO
# ============================================================================
"""
Para integrar estas extensões ao StorageManager existente:

1. Copie todos os métodos desta classe
2. Cole dentro da classe StorageManager em storage_manager.py
3. Chame _init_execution_logs_table(), _init_scheduled_tasks_table(),
   e _init_tool_configurations_table() no __init__ do StorageManager

Exemplo no __init__:
    def __init__(self):
        self.db_path = config.DB_PATH
        base_key = config.ENCRYPTION_KEY or "datamaster-local"
        self._hw_key = f"{base_key}-{SecurityManager.get_hwid()[:16]}"
        self._init_database()
        
        # Adicionar estas 3 linhas:
        self._init_execution_logs_table()
        self._init_scheduled_tasks_table()
        self._init_tool_configurations_table()
"""
