"""
UserService - Serviço de operações de usuário
Encapsula AuthManager + StorageManager para operações de sessão e autenticação.
"""
import logging
from typing import Optional, Dict

log = logging.getLogger(__name__)


class UserService:
    """Serviço que encapsula operações de autenticação e sessão do usuário."""

    def __init__(self):
        from src.core.auth.auth_manager import AuthManager
        from src.core.storage.storage_manager import StorageManager
        self._auth = AuthManager()
        self._storage = StorageManager()

    def get_current_user(self) -> Optional[Dict]:
        return self._auth.get_current_user()

    def set_current_user(self, user_data: dict):
        self._auth.set_current_user(user_data)

    def logout(self):
        self._auth.logout()
        self._storage.clear_session()

    def get_token(self) -> Optional[str]:
        return self._storage.get_token()

    def get_session(self) -> Optional[Dict]:
        return self._storage.get_saved_session()

    def clear_session(self):
        self._storage.clear_session()

    def is_session_valid(self) -> bool:
        return self._auth.is_session_valid()

    def is_plan_expired(self) -> bool:
        return self._auth.is_plan_expired()

    def get_theme(self) -> Optional[str]:
        return self._storage.get_theme()

    def save_theme(self, theme: str):
        self._storage.save_theme(theme)

    @property
    def auth_manager(self):
        return self._auth

    @property
    def storage_manager(self):
        return self._storage
