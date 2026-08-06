"""
User Storage - Gerencia sessão de usuário, tema, credenciais e preferências.
Todos os dados sensíveis são criptografados com Fernet (AES).
"""
import sqlite3
import logging
from typing import Optional, Dict
from src.core.storage.db_encryption import DBEncryption, needs_encryption

log = logging.getLogger(__name__)

# ── Colunas que NÃO devem ser criptografadas (usadas em queries) ──────────
_PLAIN_COLUMNS = {"id", "created_at", "notificacoes_email", "notificacoes_desktop", "theme", "history_retention"}

# ── Colunas que SÃO criptografadas ────────────────────────────────────────
_ENCRYPTED_COLUMNS = {"email", "plan", "expires_at", "session_token_encrypted",
                      "refresh_token_encrypted", "data_expiracao"}


class UserStorage:
    def __init__(self, db_path: str, hw_key: str, db_encryption: DBEncryption = None):
        self.db_path = db_path
        self._hw_key = hw_key
        self._enc = db_encryption or DBEncryption(password="", hwid=hw_key)

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
        return self._enc.decrypt(data)

    def save_user_session(self, user_data: Dict):
        encrypted_token = self._encrypt(user_data.get("session_token", ""))
        encrypted_refresh = self._encrypt(user_data.get("refresh_token", ""))
        encrypted_email = self._encrypt(user_data.get("email", ""))
        encrypted_plan = self._encrypt(user_data.get("plan", ""))
        encrypted_expires = self._encrypt(user_data.get("expires_at", ""))
        encrypted_data_exp = self._encrypt(user_data.get("data_expiracao", ""))

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, email, plan, expires_at, created_at,
                notificacoes_email, notificacoes_desktop, session_token_encrypted,
                refresh_token_encrypted, theme, data_expiracao, history_retention)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data.get("id"),
            encrypted_email,
            encrypted_plan,
            encrypted_expires,
            user_data.get("created_at"),
            1 if user_data.get("notificacoes_email", True) else 0,
            1 if user_data.get("notificacoes_desktop", True) else 0,
            encrypted_token,
            encrypted_refresh,
            user_data.get("theme", "system"),
            encrypted_data_exp,
            user_data.get("history_retention", "15d"),
        ))
        conn.commit()
        conn.close()

    def get_saved_session(self) -> Optional[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, plan, expires_at, session_token_encrypted,
                refresh_token_encrypted, created_at, notificacoes_email,
                notificacoes_desktop, theme, data_expiracao, history_retention
            FROM users LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        if row:
            try:
                session_token = self._decrypt(row[4]) if row[4] else ""
                refresh_token = self._decrypt(row[5]) if row[5] else ""
                email = self._decrypt(row[1]) if row[1] else ""
                plan = self._decrypt(row[2]) if row[2] else ""
                expires_at = self._decrypt(row[3]) if row[3] else ""
                data_expiracao = self._decrypt(row[10]) if row[10] else None
            except Exception:
                log.warning("Sessão antiga corrompida (chave de criptografia alterada) — limpando")
                self.clear_session()
                return None
            return {
                "id": row[0],
                "email": email,
                "plan": plan,
                "expires_at": expires_at,
                "created_at": row[6],
                "notificacoes_email": bool(row[7]),
                "notificacoes_desktop": bool(row[8]),
                "session_token": session_token,
                "refresh_token": refresh_token,
                "theme": row[9] if len(row) > 9 and row[9] else "system",
                "data_expiracao": data_expiracao,
                "history_retention": row[11] if len(row) > 11 and row[11] else "15d",
            }
        return None

    def clear_session(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def get_token(self) -> Optional[str]:
        session = self.get_saved_session()
        return session.get("session_token") if session else None

    def get_user_data(self) -> Optional[Dict]:
        return self.get_saved_session()

    def get_stored_credentials(self) -> Optional[Dict]:
        session = self.get_saved_session()
        if session and session.get("refresh_token"):
            return {"refresh_token": session["refresh_token"]}
        return None

    def save_theme(self, theme: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET theme = ? WHERE id = (SELECT id FROM users LIMIT 1)", (theme,))
        conn.commit()
        conn.close()

    def get_theme(self) -> str:
        session = self.get_saved_session()
        return session.get("theme", "system") if session else "system"

    def save_tool_theme(self, tool_key: str, theme: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                       (f"theme_{tool_key}", theme))
        conn.commit()
        conn.close()

    def get_tool_theme(self, tool_key: str) -> str:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (f"theme_{tool_key}",))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "classic_blue"

    def save_history_retention(self, retention: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET history_retention = ? WHERE id = (SELECT id FROM users LIMIT 1)",
            (retention,))
        conn.commit()
        conn.close()

    def get_history_retention(self) -> str:
        session = self.get_saved_session()
        return session.get("history_retention", "15d") if session else "15d"
