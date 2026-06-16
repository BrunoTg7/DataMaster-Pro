"""
Storage Manager - Facade that delegates to specialized storage modules.
Maintains full backward compatibility while keeping code organized.
"""
import sqlite3
import json
import os
import functools
import logging
from datetime import datetime
from typing import Optional, Dict, List
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.encryption import encrypt_data, decrypt_data, DecryptionError as EncryptionDecryptionError
from src.core.security.security_manager import SecurityManager
from src.core.storage.user_storage import UserStorage
from src.core.storage.task_storage import TaskStorage
from src.core.storage.execution_storage import ExecutionStorage
from src.core.storage.config_storage import ConfigStorage

log = logging.getLogger(__name__)


class DatabaseError(Exception):
    pass


class IntegrityError(DatabaseError):
    pass


class DecryptionError(DatabaseError):
    pass


def _safe_db(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except (IntegrityError, DecryptionError) as e:
            log.error("ERRO CRÍTICO em %s: %s", method.__name__, e, exc_info=True)
            raise
        except sqlite3.IntegrityError as e:
            log.error("IntegrityError em %s: %s", method.__name__, e, exc_info=True)
            raise IntegrityError(str(e)) from e
        except Exception as e:
            log.warning("Erro em %s: %s", method.__name__, e)
            return None
    return wrapper


class StorageManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        self._hw_key = self._derive_encryption_key()
        self._init_database()
        self._init_execution_logs_table()
        self._init_scheduled_tasks_table()
        self._init_tool_configurations_table()

        self._user = UserStorage(self.db_path, self._hw_key)
        self._tasks = TaskStorage(self.db_path)
        self._executions = ExecutionStorage(self.db_path)
        self._config = ConfigStorage(self.db_path)

    def _derive_encryption_key(self) -> str:
        env_key = config.ENCRYPTION_KEY
        if env_key and env_key != "your-secret-key-32-chars-here!" and len(env_key) >= 16:
            base_key = env_key
        else:
            key_file = os.path.join(os.path.dirname(self.db_path), ".encryption_key")
            if os.path.exists(key_file):
                with open(key_file, "r") as f:
                    base_key = f.read().strip()
                if not base_key or len(base_key) < 16:
                    base_key = os.urandom(32).hex()
                    with open(key_file, "w") as f:
                        f.write(base_key)
            else:
                base_key = os.urandom(32).hex()
                try:
                    with open(key_file, "w") as f:
                        f.write(base_key)
                    log.info("Chave de criptografia gerada e salva em %s", key_file)
                except OSError as e:
                    log.warning("Não foi possível salvar chave de criptografia: %s", e)

        hwid = SecurityManager.get_hwid()
        if not hwid or len(hwid) < 16:
            log.warning("HWID inválido, usando apenas chave local (menos seguro)")
            return base_key
        return f"{base_key}-{hwid[:16]}"

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_database(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        # ── Schema version tracking ──────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('version', '0')")
        current_version = int(
            cursor.execute("SELECT value FROM schema_meta WHERE key='version'").fetchone()[0]
        )

        # ── Users table ──────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, email TEXT, plan TEXT, expires_at TEXT,
                created_at TEXT, notificacoes_email INTEGER DEFAULT 1,
                notificacoes_desktop INTEGER DEFAULT 1, session_token_encrypted TEXT,
                refresh_token_encrypted TEXT, theme TEXT DEFAULT 'system',
                history_retention TEXT DEFAULT '15d'
            )
        """)
        _VALID_USER_COLUMNS = {
            "created_at": "TEXT", "notificacoes_email": "INTEGER DEFAULT 1",
            "notificacoes_desktop": "INTEGER DEFAULT 1", "refresh_token_encrypted": "TEXT",
            "theme": "TEXT DEFAULT 'system'", "history_retention": "TEXT DEFAULT '15d'",
            "data_expiracao": "TEXT"
        }
        existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
        for col, col_type in _VALID_USER_COLUMNS.items():
            if col not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN [{col}] {col_type}")
                except sqlite3.OperationalError:
                    pass

        # ── Executions table ─────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, tool_name TEXT,
                input_files TEXT, output_file TEXT, status TEXT, rows_processed INTEGER DEFAULT 0,
                hours_saved REAL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for col, col_type in [
            ("tempo_execucao_ms", "REAL DEFAULT 0"),
            ("tempo_economizado_minutos", "REAL DEFAULT 0"),
        ]:
            try:
                cursor.execute(f"ALTER TABLE executions ADD COLUMN [{col}] {col_type}")
            except sqlite3.OperationalError:
                pass

        # ── Tasks table ──────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, tool_name TEXT NOT NULL, tool_display_name TEXT,
                status TEXT DEFAULT 'pending', progress_percent INTEGER DEFAULT 0,
                progress_message TEXT, input_params TEXT, output_path TEXT, log_text TEXT,
                rows_processed INTEGER DEFAULT 0, hours_saved REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP, user_id TEXT, error_message TEXT
            )
        """)
        for col, col_type in {"tool_display_name": "TEXT"}.items():
            existing_task_cols = {row[1] for row in cursor.execute("PRAGMA table_info(tasks)").fetchall()}
            if col not in existing_task_cols:
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN [{col}] {col_type}")
                except sqlite3.OperationalError:
                    pass

        # ── Settings table ───────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)
        """)

        # ── Indices ──────────────────────────────────────────────────────
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_executions_user ON executions(user_id, created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, created_at DESC)")

        # ── Bump schema version ──────────────────────────────────────────
        NEW_VERSION = 3
        if current_version < NEW_VERSION:
            if current_version < 3:
                self._migrate_column_rename(conn)
            cursor.execute("UPDATE schema_meta SET value=? WHERE key='version'", (str(NEW_VERSION),))
            log.info("Schema migrado: v%d → v%d", current_version, NEW_VERSION)

        conn.commit()
        conn.close()

    def _migrate_column_rename(self, conn):
        """Renomeia password_encrypted para refresh_token_encrypted."""
        cursor = conn.cursor()
        
        # Verificar se coluna antiga existe
        cols = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
        
        if "password_encrypted" in cols and "refresh_token_encrypted" not in cols:
            try:
                # Criar tabela temporária com novo nome de coluna
                cursor.execute("""
                    CREATE TABLE users_backup AS 
                    SELECT id, email, plan, expires_at, created_at,
                           notificacoes_email, notificacoes_desktop,
                           session_token_encrypted, password_encrypted as refresh_token_encrypted,
                           theme, data_expiracao, history_retention
                    FROM users
                """)
                
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_backup RENAME TO users")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON users(id)")
                
                log.info("Migração: password_encrypted → refresh_token_encrypted concluída")
            except Exception as e:
                log.error("Erro na migração de coluna: %s", e)
                # Se falhar, tentar recriar tabela original
                try:
                    cursor.execute("DROP TABLE IF EXISTS users_backup")
                except Exception:
                    pass

    def _init_execution_logs_table(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs_local (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, tool_name TEXT,
                status TEXT, details_json TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_elog_user ON execution_logs_local(user_id, created_at DESC)")
        conn.commit()
        conn.close()

    def _init_scheduled_tasks_table(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks_local (
                task_id TEXT PRIMARY KEY, user_id TEXT, tool_name TEXT,
                tool_action TEXT, task_name TEXT, input_files_json TEXT,
                schedule_frequency TEXT, cron_expression TEXT, next_run_at TEXT,
                enabled INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stask_user ON scheduled_tasks_local(user_id, enabled)")
        conn.commit()
        conn.close()

    def _init_tool_configurations_table(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_configurations_local (
                tool_key TEXT NOT NULL, config_name TEXT NOT NULL, config_json TEXT,
                is_default INTEGER DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (tool_key, config_name)
            )
        """)
        conn.commit()
        conn.close()

    # ── User Storage (delegation) ──────────────────────────────
    @_safe_db
    def save_user_session(self, user_data: Dict):
        return self._user.save_user_session(user_data)

    @_safe_db
    def get_saved_session(self) -> Optional[Dict]:
        return self._user.get_saved_session()

    @_safe_db
    def get_token(self) -> Optional[str]:
        return self._user.get_token()

    @_safe_db
    def get_user_data(self) -> Optional[Dict]:
        return self._user.get_user_data()

    @_safe_db
    def get_stored_credentials(self) -> Optional[Dict]:
        return self._user.get_stored_credentials()

    @_safe_db
    def clear_session(self):
        return self._user.clear_session()

    @_safe_db
    def save_theme(self, theme: str):
        return self._user.save_theme(theme)

    @_safe_db
    def get_theme(self) -> str:
        return self._user.get_theme()

    @_safe_db
    def save_tool_theme(self, tool_key: str, theme: str):
        return self._user.save_tool_theme(tool_key, theme)

    @_safe_db
    def get_tool_theme(self, tool_key: str) -> str:
        return self._user.get_tool_theme(tool_key)

    @_safe_db
    def save_history_retention(self, retention: str):
        return self._user.save_history_retention(retention)

    @_safe_db
    def get_history_retention(self) -> str:
        return self._user.get_history_retention()

    # ── Task Storage (delegation) ──────────────────────────────
    @_safe_db
    def save_task(self, task_data: dict):
        return self._tasks.save_task(task_data)

    @_safe_db
    def get_task(self, task_id: str) -> Optional[dict]:
        return self._tasks.get_task(task_id)

    @_safe_db
    def get_all_tasks(self, status_filter: str = None, limit: int = 100) -> List[dict]:
        return self._tasks.get_all_tasks(status_filter, limit)

    @_safe_db
    def get_active_tasks(self) -> List[dict]:
        return self._tasks.get_active_tasks()

    @_safe_db
    def update_task(self, task_id: str, updates: dict):
        return self._tasks.update_task(task_id, updates)

    @_safe_db
    def delete_task(self, task_id: str):
        return self._tasks.delete_task(task_id)

    @_safe_db
    def get_running_task_by_tool(self, tool_name: str) -> Optional[dict]:
        return self._tasks.get_running_task_by_tool(tool_name)

    @_safe_db
    def get_last_task_by_tool(self, tool_name: str, exclude_failed: bool = True) -> Optional[dict]:
        return self._tasks.get_last_task_by_tool(tool_name, exclude_failed)

    @_safe_db
    def get_running_tasks_count(self) -> int:
        return self._tasks.get_running_tasks_count()

    @_safe_db
    def cleanup_old_tasks(self, days: int = 7):
        return self._tasks.cleanup_old_tasks(days)

    # ── Execution Storage (delegation) ─────────────────────────
    @_safe_db
    def save_execution(self, user_id: str, tool_name: str, input_files: List[str],
                       output_file: str, rows_processed: int = 0, hours_saved: float = 0):
        return self._executions.save_execution(user_id, tool_name, input_files, output_file, rows_processed, hours_saved)

    @_safe_db
    def replace_user_executions(self, user_id: str, records: List[Dict]):
        return self._executions.replace_user_executions(user_id, records)

    @_safe_db
    def get_executions(self, user_id: str, limit: int = 100) -> List[Dict]:
        return self._executions.get_executions(user_id, limit)

    @_safe_db
    def cleanup_executions_duplicates(self):
        return self._executions.cleanup_executions_duplicates()

    @_safe_db
    def save_execution_log(self, user_id: str, tool_name: str, status: str, details: dict = None):
        return self._executions.save_execution_log(user_id, tool_name, status, details)

    @_safe_db
    def get_execution_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        return self._executions.get_execution_logs(user_id, limit)

    # ── Config Storage (delegation) ────────────────────────────
    @_safe_db
    def save_tool_configuration(self, tool_key: str, config_data: dict, is_default: bool = False):
        return self._config.save_tool_configuration(tool_key, config_data, is_default)

    @_safe_db
    def get_tool_configurations(self, tool_key: str) -> List[dict]:
        return self._config.get_tool_configurations(tool_key)

    @_safe_db
    def get_default_configuration(self, tool_key: str) -> Optional[dict]:
        return self._config.get_default_configuration(tool_key)

    @_safe_db
    def delete_tool_configuration(self, tool_key: str, config_name: str):
        return self._config.delete_tool_configuration(tool_key, config_name)

    @_safe_db
    def set_default_configuration(self, tool_key: str, config_name: str):
        return self._config.set_default_configuration(tool_key, config_name)

    @_safe_db
    def save_scheduled_task(self, task_data: dict):
        return self._config.save_scheduled_task(task_data)

    @_safe_db
    def get_scheduled_tasks(self, user_id: str) -> List[dict]:
        return self._config.get_scheduled_tasks(user_id)

    @_safe_db
    def update_scheduled_task(self, task_id: str, updates: dict):
        return self._config.update_scheduled_task(task_id, updates)

    @_safe_db
    def disable_scheduled_task(self, task_id: str):
        return self._config.disable_scheduled_task(task_id)

    @_safe_db
    def delete_scheduled_task(self, task_id: str):
        return self._config.delete_scheduled_task(task_id)

    def get_all_scheduled_tasks(self, user_id: str) -> List[dict]:
        return self._config.get_all_scheduled_tasks(user_id)

    def replace_scheduled_tasks_for_user(self, user_id: str, tasks: List[dict]):
        return self._config.replace_scheduled_tasks_for_user(user_id, tasks)
