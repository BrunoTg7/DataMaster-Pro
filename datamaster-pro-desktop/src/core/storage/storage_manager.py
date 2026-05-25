"""
Storage Manager - Local SQLite database + encryption
"""
import sqlite3
import json
import os
import functools
import logging
from typing import Optional, Dict, List
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.encryption import encrypt_data, decrypt_data
from src.core.security.security_manager import SecurityManager

log = logging.getLogger(__name__)


def _safe_db(method):
    """Decorator: envolve metodos de banco com try/except e log"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            log.error("Erro em %s: %s", method.__name__, e)
            return None
    return wrapper


class StorageManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        base_key = config.ENCRYPTION_KEY or "datamaster-local"
        self._hw_key = f"{base_key}-{SecurityManager.get_hwid()[:16]}"
        self._init_database()

    def _encrypt(self, data: str) -> str:
        """Criptografia amarrada ao hardware"""
        return encrypt_data(data, key=self._hw_key)

    def _decrypt(self, data: str) -> str:
        """Descriptografia amarrada ao hardware"""
        return decrypt_data(data, key=self._hw_key)

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_database(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT,
                plan TEXT,
                expires_at TEXT,
                created_at TEXT,
                notificacoes_email INTEGER DEFAULT 1,
                notificacoes_desktop INTEGER DEFAULT 1,
                session_token_encrypted TEXT,
                password_encrypted TEXT,
                theme TEXT DEFAULT 'system',
                history_retention TEXT DEFAULT '15d'
            )
        """)

        # Migrações: Adicionar colunas se não existirem
        columns_to_add = {
            "created_at": "TEXT",
            "notificacoes_email": "INTEGER DEFAULT 1",
            "notificacoes_desktop": "INTEGER DEFAULT 1",
            "password_encrypted": "TEXT",
            "theme": "TEXT DEFAULT 'system'",
            "history_retention": "TEXT DEFAULT '15d'"
        }
        
        for col, col_type in columns_to_add.items():
            try:
                cursor.execute(f"SELECT {col} FROM users LIMIT 1")
            except sqlite3.OperationalError:
                log.info(f"Adicionando coluna {col} à tabela users...")
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                except sqlite3.OperationalError as e:
                    log.warning(f"Coluna {col} pode já existir: {e}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                tool_name TEXT,
                input_files TEXT,
                output_file TEXT,
                status TEXT,
                rows_processed INTEGER DEFAULT 0,
                hours_saved REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Adicionar colunas se não existirem
        try:
            cursor.execute("SELECT rows_processed FROM executions LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE executions ADD COLUMN rows_processed INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE executions ADD COLUMN hours_saved REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                tool_name TEXT,
                config_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                tool_name TEXT NOT NULL,
                tool_display_name TEXT,
                status TEXT DEFAULT 'pending',
                progress_percent INTEGER DEFAULT 0,
                progress_message TEXT,
                input_params TEXT,
                output_path TEXT,
                log_text TEXT,
                rows_processed INTEGER DEFAULT 0,
                hours_saved REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                user_id TEXT,
                error_message TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Migração: adicionar colunas que podem não existir em DBs antigos
        col_migrations = [
            ("tasks", "tool_display_name", "TEXT"),
        ]
        for table, col, col_type in col_migrations:
            try:
                cursor.execute(f"SELECT {col} FROM {table} LIMIT 1")
            except sqlite3.OperationalError:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                    log.info(f"Adicionada coluna {col} à tabela {table}")
                except sqlite3.OperationalError:
                    pass

        conn.commit()
        conn.close()

    @_safe_db
    def save_user_session(self, user_data: Dict):
        encrypted_token = self._encrypt(user_data.get("session_token", ""))
        encrypted_password = self._encrypt(user_data.get("password", ""))

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO users (id, email, plan, expires_at, created_at, notificacoes_email, notificacoes_desktop, session_token_encrypted, password_encrypted, theme)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data.get("id"),
            user_data.get("email"),
            user_data.get("plan"),
            user_data.get("expires_at"),
            user_data.get("created_at"),
            1 if user_data.get("notificacoes_email", True) else 0,
            1 if user_data.get("notificacoes_desktop", True) else 0,
            encrypted_token,
            encrypted_password,
            user_data.get("theme", "system")
        ))

        conn.commit()
        conn.close()

    @_safe_db
    def get_saved_session(self) -> Optional[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, email, plan, expires_at, session_token_encrypted, password_encrypted, created_at, notificacoes_email, notificacoes_desktop, theme
            FROM users LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            session_token = self._decrypt(row[4]) if row[4] else ""
            password = self._decrypt(row[5]) if row[5] else ""
            return {
                "id": row[0],
                "email": row[1],
                "plan": row[2],
                "expires_at": row[3],
                "created_at": row[6],
                "notificacoes_email": bool(row[7]),
                "notificacoes_desktop": bool(row[8]),
                "session_token": session_token,
                "password": password,
                "theme": row[9] if len(row) > 9 and row[9] else "system"
            }
        return None

    @_safe_db
    def save_execution(self, user_id: str, tool_name: str, input_files: List[str], 
                       output_file: str, rows_processed: int = 0, hours_saved: float = 0):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO executions (user_id, tool_name, input_files, output_file, status, rows_processed, hours_saved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            tool_name,
            json.dumps(input_files),
            output_file,
            "completed",
            rows_processed,
            hours_saved
        ))

        conn.commit()
        conn.close()

    @_safe_db
    def replace_user_executions(self, user_id: str, records: List[Dict]):
        """Substitui TODAS as execucoes locais do usuario pelos registros do remoto.
        
        Apaga tudo do usuario e reinsere os registros fornecidos.
        Assim o SQLite local vira um espelho fiel do Supabase durante o sync.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM executions WHERE user_id = ?", (user_id,))
        for rec in records:
            cursor.execute("""
                INSERT INTO executions (user_id, tool_name, input_files, output_file,
                                        status, rows_processed, hours_saved, created_at)
                VALUES (?, ?, '[]', '', 'completed', ?, ?, ?)
            """, (
                user_id,
                rec.get("ferramenta", "unknown"),
                rec.get("linhas_processadas", 0),
                rec.get("tempo_economizado_minutos", 0) / 60,
                rec.get("created_at", ""),
            ))
        conn.commit()
        conn.close()

    @_safe_db
    def get_executions(self, user_id: str, limit: int = 50) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, tool_name, input_files, output_file, status, created_at, rows_processed, hours_saved
            FROM executions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "tool_name": row[1],
                "input_files": json.loads(row[2]) if row[2] else [],
                "output_file": row[3],
                "status": row[4],
                "created_at": row[5],
                "rows_processed": row[6],
                "hours_saved": row[7]
            }
            for row in rows
        ]

    @_safe_db
    def get_token(self) -> Optional[str]:
        session = self.get_saved_session()
        return session.get("session_token") if session else None

    @_safe_db
    def get_user_data(self) -> Optional[Dict]:
        return self.get_saved_session()

    @_safe_db
    def save_theme(self, theme: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET theme = ? WHERE id = (SELECT id FROM users LIMIT 1)", (theme,))
        conn.commit()
        conn.close()

    @_safe_db
    def get_theme(self) -> str:
        session = self.get_saved_session()
        return session.get("theme", "system") if session else "system"

    @_safe_db
    def save_tool_theme(self, tool_key: str, theme: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (f"theme_{tool_key}", theme))
        conn.commit()
        conn.close()

    @_safe_db
    def get_tool_theme(self, tool_key: str) -> str:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (f"theme_{tool_key}",))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "classic_blue"

    @_safe_db
    def save_history_retention(self, retention: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET history_retention = ? WHERE id = (SELECT id FROM users LIMIT 1)", (retention,))
        conn.commit()
        conn.close()

    @_safe_db
    def get_history_retention(self) -> str:
        session = self.get_saved_session()
        return session.get("history_retention", "15d") if session else "15d"

    @_safe_db
    def get_stored_credentials(self) -> Optional[Dict]:
        """Retorna email e senha descriptografados do usuario logado."""
        session = self.get_saved_session()
        if session and session.get("email") and session.get("password"):
            return {"email": session["email"], "password": session["password"]}
        return None

    @_safe_db
    def clear_session(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    @_safe_db
    def save_task(self, task_data: dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, tool_name, tool_display_name, status, progress_percent, progress_message, 
                            input_params, output_path, log_text, rows_processed, hours_saved, 
                            created_at, updated_at, user_id, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_data.get("id"),
            task_data.get("tool_name"),
            task_data.get("tool_display_name"),
            task_data.get("status", "pending"),
            task_data.get("progress_percent", 0),
            task_data.get("progress_message", ""),
            task_data.get("input_params", ""),
            task_data.get("output_path", ""),
            task_data.get("log_text", ""),
            task_data.get("rows_processed", 0),
            task_data.get("hours_saved", 0),
            task_data.get("created_at", ""),
            task_data.get("updated_at", ""),
            task_data.get("user_id", ""),
            task_data.get("error_message", "")
        ))
        conn.commit()
        conn.close()

    @_safe_db
    def get_task(self, task_id: str) -> Optional[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tool_name, status, progress_percent, progress_message, input_params,
                   output_path, log_text, rows_processed, hours_saved, created_at, 
                   updated_at, completed_at, user_id, error_message, tool_display_name
            FROM tasks WHERE id = ?
        """, (task_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "tool_name": row[1],
                "status": row[2],
                "progress_percent": row[3],
                "progress_message": row[4],
                "input_params": row[5],
                "output_path": row[6],
                "log_text": row[7],
                "rows_processed": row[8],
                "hours_saved": row[9],
                "created_at": row[10],
                "updated_at": row[11],
                "completed_at": row[12],
                "user_id": row[13],
                "error_message": row[14],
                "tool_display_name": row[15]
            }
        return None

    @_safe_db
    def get_all_tasks(self, status_filter: str = None, limit: int = 100) -> List[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        if status_filter:
            cursor.execute("""
                SELECT id, tool_name, status, progress_percent, progress_message, input_params,
                       output_path, log_text, rows_processed, hours_saved, created_at, 
                       updated_at, completed_at, user_id, error_message, tool_display_name
                FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?
            """, (status_filter, limit))
        else:
            cursor.execute("""
                SELECT id, tool_name, status, progress_percent, progress_message, input_params,
                       output_path, log_text, rows_processed, hours_saved, created_at, 
                       updated_at, completed_at, user_id, error_message, tool_display_name
                FROM tasks ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": row[0],
                "tool_name": row[1],
                "status": row[2],
                "progress_percent": row[3],
                "progress_message": row[4],
                "input_params": row[5],
                "output_path": row[6],
                "log_text": row[7],
                "rows_processed": row[8],
                "hours_saved": row[9],
                "created_at": row[10],
                "updated_at": row[11],
                "completed_at": row[12],
                "user_id": row[13],
                "error_message": row[14],
                "tool_display_name": row[15]
            }
            for row in rows
        ]

    @_safe_db
    def get_active_tasks(self) -> List[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tool_name, status, progress_percent, progress_message, input_params,
                   output_path, log_text, rows_processed, hours_saved, created_at, 
                   updated_at, completed_at, user_id, error_message, tool_display_name
            FROM tasks WHERE status IN ('pending', 'running') ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": row[0],
                "tool_name": row[1],
                "status": row[2],
                "progress_percent": row[3],
                "progress_message": row[4],
                "input_params": row[5],
                "output_path": row[6],
                "log_text": row[7],
                "rows_processed": row[8],
                "hours_saved": row[9],
                "created_at": row[10],
                "updated_at": row[11],
                "completed_at": row[12],
                "user_id": row[13],
                "error_message": row[14],
                "tool_display_name": row[15]
            }
            for row in rows
        ]

    _ALLOWED_TASK_COLUMNS = {
        "tool_name", "tool_display_name", "status", "progress_percent",
        "progress_message", "input_params", "output_path", "log_text",
        "rows_processed", "hours_saved", "completed_at", "user_id", "error_message"
    }

    @_safe_db
    def update_task(self, task_id: str, updates: dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        set_clauses = []
        values = []
        for key, value in updates.items():
            if key not in self._ALLOWED_TASK_COLUMNS:
                continue
            set_clauses.append(f"{key} = ?")
            values.append(value)
        if not set_clauses:
            conn.close()
            return
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.append(task_id)
        cursor.execute(f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?", values)
        conn.commit()
        conn.close()

    @_safe_db
    def delete_task(self, task_id: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

    @_safe_db
    def get_running_task_by_tool(self, tool_name: str) -> Optional[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tool_name, status FROM tasks 
            WHERE tool_name = ? AND status IN ('pending', 'running')
        """, (tool_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "tool_name": row[1], "status": row[2]}
        return None

    @_safe_db
    def get_last_task_by_tool(self, tool_name: str, exclude_failed: bool = True) -> Optional[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        if exclude_failed:
            cursor.execute("""
                SELECT id, tool_name, status, progress_percent, progress_message, input_params,
                       output_path, log_text, rows_processed, hours_saved, created_at, 
                       updated_at, completed_at, user_id, error_message, tool_display_name
                FROM tasks WHERE tool_name = ? AND status NOT IN ('failed', 'interrupted')
                ORDER BY created_at DESC LIMIT 1
            """, (tool_name,))
        else:
            cursor.execute("""
                SELECT id, tool_name, status, progress_percent, progress_message, input_params,
                       output_path, log_text, rows_processed, hours_saved, created_at, 
                       updated_at, completed_at, user_id, error_message, tool_display_name
                FROM tasks WHERE tool_name = ?
                ORDER BY created_at DESC LIMIT 1
            """, (tool_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "tool_name": row[1],
                "status": row[2],
                "progress_percent": row[3],
                "progress_message": row[4],
                "input_params": row[5],
                "output_path": row[6],
                "log_text": row[7],
                "rows_processed": row[8],
                "hours_saved": row[9],
                "created_at": row[10],
                "updated_at": row[11],
                "completed_at": row[12],
                "user_id": row[13],
                "error_message": row[14],
                "tool_display_name": row[15]
            }
        return None

    @_safe_db
    def get_running_tasks_count(self) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('pending', 'running')")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    @_safe_db
    def cleanup_old_tasks(self, days: int = 7):
        """Remove tarefas concluídas/falhas/canceladas com mais de N dias"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM tasks
            WHERE status IN ('completed', 'failed', 'cancelled', 'interrupted')
              AND julianday('now') - julianday(updated_at) > ?
        """, (days,))
        removed = cursor.rowcount
        conn.commit()
        conn.close()
        if removed > 0:
            log.info(f"Limpeza: {removed} tarefas antigas removidas")

    @_safe_db
    def cleanup_executions_duplicates(self):
        """Remove execuções duplicadas (mesmo tool_name + created_at) mantendo a mais recente"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM executions WHERE id NOT IN (
                SELECT MIN(id) FROM executions GROUP BY user_id, tool_name, created_at
            )
        """)
        removed = cursor.rowcount
        conn.commit()
        conn.close()
        if removed > 0:
            log.info(f"Limpeza: {removed} execuções duplicadas removidas")