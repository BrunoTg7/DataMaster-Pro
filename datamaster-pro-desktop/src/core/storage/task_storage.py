"""
Task Storage - Gerencia CRUD de tarefas.
Campos sensíveis são criptografados com Fernet (AES).
"""
import sqlite3
import logging
from typing import Optional, List
from src.core.storage.db_encryption import DBEncryption, needs_encryption

log = logging.getLogger(__name__)

# ── Colunas que SÃO criptografadas ────────────────────────────────────────
_ENCRYPTED_COLS = {"input_params", "output_path", "log_text", "error_message", "progress_message"}


class TaskStorage:
    def __init__(self, db_path: str, db_encryption: DBEncryption = None):
        self.db_path = db_path
        self._enc = db_encryption or DBEncryption()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _encrypt(self, data: str) -> str:
        if not data:
            return ""
        return self._enc.encrypt(str(data))

    def _decrypt(self, data: str) -> str:
        if not data:
            return ""
        try:
            return self._enc.decrypt(data)
        except Exception:
            return data

    _ALLOWED_COLUMNS = {
        "tool_name", "tool_display_name", "status", "progress_percent",
        "progress_message", "input_params", "output_path", "log_text",
        "rows_processed", "hours_saved", "completed_at", "user_id", "error_message"
    }

    _COLUMNS = """id, tool_name, status, progress_percent, progress_message, input_params,
                   output_path, log_text, rows_processed, hours_saved, created_at,
                   updated_at, completed_at, user_id, error_message, tool_display_name"""

    def _row_to_dict(self, row) -> dict:
        return {
            "id": row[0], "tool_name": row[1], "status": row[2],
            "progress_percent": row[3], "progress_message": self._decrypt(row[4]),
            "input_params": self._decrypt(row[5]), "output_path": self._decrypt(row[6]),
            "log_text": self._decrypt(row[7]),
            "rows_processed": row[8], "hours_saved": row[9],
            "created_at": row[10], "updated_at": row[11], "completed_at": row[12],
            "user_id": row[13], "error_message": self._decrypt(row[14]),
            "tool_display_name": row[15]
        }

    def save_task(self, task_data: dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, tool_name, tool_display_name, status, progress_percent,
                progress_message, input_params, output_path, log_text, rows_processed,
                hours_saved, created_at, updated_at, completed_at, user_id, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_data.get("id"), task_data.get("tool_name"),
            task_data.get("tool_display_name"), task_data.get("status", "pending"),
            task_data.get("progress_percent", 0),
            self._encrypt(task_data.get("progress_message", "")),
            self._encrypt(task_data.get("input_params", "")),
            self._encrypt(task_data.get("output_path", "")),
            self._encrypt(task_data.get("log_text", "")),
            task_data.get("rows_processed", 0),
            task_data.get("hours_saved", 0), task_data.get("created_at", ""),
            task_data.get("updated_at", ""), task_data.get("completed_at"),
            task_data.get("user_id", ""),
            self._encrypt(task_data.get("error_message", ""))
        ))
        conn.commit()
        conn.close()

    def get_task(self, task_id: str) -> Optional[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {self._COLUMNS} FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def get_all_tasks(self, status_filter: str = None, limit: int = 100) -> List[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        if status_filter:
            cursor.execute(f"SELECT {self._COLUMNS} FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status_filter, limit))
        else:
            cursor.execute(f"SELECT {self._COLUMNS} FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def get_active_tasks(self) -> List[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {self._COLUMNS} FROM tasks WHERE status IN ('pending', 'running') ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def update_task(self, task_id: str, updates: dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        set_clauses = []
        values = []
        for key, value in updates.items():
            if key not in self._ALLOWED_COLUMNS:
                continue
            if key in _ENCRYPTED_COLS:
                value = self._encrypt(str(value))
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

    def delete_task(self, task_id: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

    def get_running_task_by_tool(self, tool_name: str) -> Optional[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tool_name, status FROM tasks WHERE tool_name = ? AND status IN ('pending', 'running')",
            (tool_name,))
        row = cursor.fetchone()
        conn.close()
        return {"id": row[0], "tool_name": row[1], "status": row[2]} if row else None

    def get_last_task_by_tool(self, tool_name: str, exclude_failed: bool = True) -> Optional[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        if exclude_failed:
            cursor.execute(
                f"SELECT {self._COLUMNS} FROM tasks WHERE tool_name = ? AND status NOT IN ('failed', 'interrupted') ORDER BY created_at DESC LIMIT 1",
                (tool_name,))
        else:
            cursor.execute(
                f"SELECT {self._COLUMNS} FROM tasks WHERE tool_name = ? ORDER BY created_at DESC LIMIT 1",
                (tool_name,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def get_running_tasks_count(self) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('pending', 'running')")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def cleanup_old_tasks(self, days: int = 7):
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
            log.info("Limpeza: %d tarefas antigas removidas", removed)
        return removed
