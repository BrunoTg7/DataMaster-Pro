"""
Storage Manager - Local SQLite database + encryption
"""
import sqlite3
import json
import os
from typing import Optional, Dict, List
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.encryption import encrypt_data, decrypt_data
from src.core.security.security_manager import SecurityManager

class StorageManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        # Gera uma chave dinâmica amarrada ao Hardware deste PC
        self._hw_key = f"{config.ENCRYPTION_KEY}-{SecurityManager.get_hwid()[:16]}"
        self._init_database()

    def _encrypt(self, data: str) -> str:
        """Criptografia amarrada ao hardware"""
        return encrypt_data(data, key=self._hw_key)

    def _decrypt(self, data: str) -> str:
        """Descriptografia amarrada ao hardware"""
        return decrypt_data(data, key=self._hw_key)

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
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
                theme TEXT DEFAULT 'system'
            )
        """)

        # Migrações: Adicionar colunas se não existirem
        columns_to_add = {
            "created_at": "TEXT",
            "notificacoes_email": "INTEGER DEFAULT 1",
            "notificacoes_desktop": "INTEGER DEFAULT 1",
            "password_encrypted": "TEXT",
            "theme": "TEXT DEFAULT 'system'"
        }
        
        for col, col_type in columns_to_add.items():
            try:
                cursor.execute(f"SELECT {col} FROM users LIMIT 1")
            except sqlite3.OperationalError:
                print(f"[DB] Adicionando coluna {col} à tabela users...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")

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
            cursor.execute("ALTER TABLE executions ADD COLUMN rows_processed INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE executions ADD COLUMN hours_saved REAL DEFAULT 0")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                tool_name TEXT,
                config_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def save_user_session(self, user_data: Dict):
        encrypted_token = self._encrypt(user_data.get("session_token", ""))
        encrypted_password = self._encrypt(user_data.get("password", ""))

        conn = sqlite3.connect(self.db_path)
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

    def get_saved_session(self) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
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

    def save_execution(self, user_id: str, tool_name: str, input_files: List[str], 
                       output_file: str, rows_processed: int = 0, hours_saved: float = 0):
        conn = sqlite3.connect(self.db_path)
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

    def get_executions(self, user_id: str, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
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

    def get_token(self) -> Optional[str]:
        session = self.get_saved_session()
        return session.get("session_token") if session else None

    def get_user_data(self) -> Optional[Dict]:
        return self.get_saved_session()

    def save_theme(self, theme: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET theme = ? WHERE id = (SELECT id FROM users LIMIT 1)", (theme,))
        conn.commit()
        conn.close()

    def get_theme(self) -> str:
        session = self.get_saved_session()
        return session.get("theme", "system") if session else "system"

    def clear_session(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()