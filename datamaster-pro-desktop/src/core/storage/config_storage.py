"""
Config Storage - Gerencia configurações de ferramentas e tarefas agendadas.
Campos sensíveis são criptografados com Fernet (AES).
"""
import sqlite3
import json
import logging
from typing import Optional, List
from src.core.storage.db_encryption import DBEncryption, needs_encryption

log = logging.getLogger(__name__)


class ConfigStorage:
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
        return self._enc.encrypt(data)

    def _decrypt(self, data: str) -> str:
        if not data:
            return ""
        try:
            return self._enc.decrypt(data)
        except Exception:
            return data

    def _encrypt_json(self, obj) -> str:
        return self._enc.encrypt_json(obj)

    def _decrypt_json(self, data: str):
        return self._enc.decrypt_json(data)

    def save_tool_configuration(self, tool_key: str, config_data: dict, is_default: bool = False):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO tool_configurations_local
                (tool_key, config_name, config_json, is_default, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            tool_key, config_data.get("name", "default"),
            self._encrypt_json(config_data),
            1 if is_default else 0
        ))
        conn.commit()
        conn.close()

    def get_tool_configurations(self, tool_key: str) -> List[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT config_name, config_json, is_default, updated_at
            FROM tool_configurations_local WHERE tool_key = ?
            ORDER BY is_default DESC, config_name
        """, (tool_key,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {"name": r[0], "config": self._decrypt_json(r[1]) or {}, "is_default": bool(r[2]), "updated_at": r[3]}
            for r in rows
        ]

    def get_default_configuration(self, tool_key: str) -> Optional[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT config_json FROM tool_configurations_local
            WHERE tool_key = ? AND is_default = 1
        """, (tool_key,))
        row = cursor.fetchone()
        conn.close()
        return self._decrypt_json(row[0]) if row and row[0] else None

    def delete_tool_configuration(self, tool_key: str, config_name: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM tool_configurations_local
            WHERE tool_key = ? AND config_name = ?
        """, (tool_key, config_name))
        conn.commit()
        conn.close()

    def set_default_configuration(self, tool_key: str, config_name: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE tool_configurations_local SET is_default = 0 WHERE tool_key = ?", (tool_key,))
        cursor.execute("""
            UPDATE tool_configurations_local SET is_default = 1
            WHERE tool_key = ? AND config_name = ?
        """, (tool_key, config_name))
        conn.commit()
        conn.close()

    def save_scheduled_task(self, task_data: dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO scheduled_tasks_local
                (task_id, user_id, tool_name, tool_action, task_name,
                 input_files_json, schedule_frequency, cron_expression,
                 next_run_at, enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            task_data.get("task_id"), task_data.get("user_id"),
            task_data.get("tool_name"), task_data.get("tool_action"),
            self._encrypt(task_data.get("task_name", "")),
            self._encrypt_json(task_data.get("input_files", [])),
            task_data.get("schedule_frequency"), task_data.get("cron_expression"),
            task_data.get("next_run_at"),
            1 if task_data.get("enabled", True) else 0,
            task_data.get("created_at"),
        ))
        conn.commit()
        conn.close()

    def get_scheduled_tasks(self, user_id: str) -> List[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT task_id, tool_name, tool_action, task_name,
                input_files_json, schedule_frequency, cron_expression,
                next_run_at, enabled, created_at, updated_at
            FROM scheduled_tasks_local WHERE user_id = ? AND enabled = 1
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "task_id": r[0], "user_id": user_id, "tool_name": r[1],
                "tool_action": r[2], "task_name": self._decrypt(r[3]),
                "input_files": self._decrypt_json(r[4]) or [],
                "schedule_frequency": r[5], "cron_expression": r[6],
                "next_run_at": r[7], "enabled": bool(r[8]),
                "created_at": r[9], "updated_at": r[10]
            }
            for r in rows
        ]

    def update_scheduled_task(self, task_id: str, updates: dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        clauses = []
        values = []
        for k, v in updates.items():
            if k in ("next_run_at", "enabled", "task_name", "schedule_frequency", "cron_expression"):
                if k == "task_name":
                    v = self._encrypt(str(v))
                clauses.append(f"{k} = ?")
                values.append(v)
        if clauses:
            clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(task_id)
            cursor.execute(f"UPDATE scheduled_tasks_local SET {', '.join(clauses)} WHERE task_id = ?", values)
            conn.commit()
        conn.close()

    def disable_scheduled_task(self, task_id: str):
        self.update_scheduled_task(task_id, {"enabled": False})

    def delete_scheduled_task(self, task_id: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_tasks_local WHERE task_id = ?", (task_id,))
        conn.commit()
        conn.close()

    def get_all_scheduled_tasks(self, user_id: str) -> List[dict]:
        return self.get_scheduled_tasks(user_id)

    def replace_scheduled_tasks_for_user(self, user_id: str, tasks: List[dict]):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_tasks_local WHERE user_id = ?", (user_id,))
        for task in tasks:
            cursor.execute("""
                INSERT OR REPLACE INTO scheduled_tasks_local
                    (task_id, user_id, tool_name, tool_action, task_name,
                     input_files_json, schedule_frequency, cron_expression,
                     next_run_at, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.get("task_id"), user_id,
                task.get("tool_name"), task.get("tool_action"),
                self._encrypt(task.get("task_name", "")),
                self._encrypt_json(task.get("input_files", task.get("input_files_json", []))),
                task.get("schedule_frequency"), task.get("cron_expression"),
                task.get("next_run_at"),
                1 if task.get("enabled", True) else 0,
                task.get("created_at"), task.get("updated_at"),
            ))
        conn.commit()
        conn.close()
