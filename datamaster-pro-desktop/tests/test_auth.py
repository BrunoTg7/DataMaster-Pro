import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.auth.auth_manager import AuthManager


class TestAuthManager:

    @pytest.fixture
    def auth_manager(self):
        return AuthManager()

    def test_initial_state(self, auth_manager):
        assert auth_manager.current_user is None
        assert auth_manager._session_token is None

    def test_logout_clears_session(self, auth_manager):
        auth_manager.current_user = {"email": "test@test.com"}
        auth_manager._session_token = "fake_token"

        auth_manager.logout()

        assert auth_manager.current_user is None
        assert auth_manager._session_token is None

    def test_get_current_user_none(self, auth_manager):
        assert auth_manager.get_current_user() is None

    def test_set_current_user(self, auth_manager):
        user_data = {"email": "test@test.com", "plan": "pro"}
        auth_manager.set_current_user(user_data)

        assert auth_manager.get_current_user() == user_data

    def test_is_session_valid_false_no_user(self, auth_manager):
        assert auth_manager.is_session_valid() is False

    def test_is_session_valid_expired(self, auth_manager):
        auth_manager.current_user = {
            "email": "test@test.com",
            "expires_at": (datetime.now() - timedelta(days=1)).isoformat()
        }

        assert auth_manager.is_session_valid() is False

    def test_is_session_valid_not_expired(self, auth_manager):
        auth_manager.current_user = {
            "email": "test@test.com",
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }

        assert auth_manager.is_session_valid() is True

    def test_is_session_valid_invalid_format(self, auth_manager):
        auth_manager.current_user = {
            "email": "test@test.com",
            "expires_at": "invalid-date"
        }

        assert auth_manager.is_session_valid() is False


class TestAuthManagerLogin:
    """Testes de login (sem mock real)"""

    def test_login_requires_supabase(self):
        """Testa que login requer Supabase configurado"""
        auth_manager = AuthManager()

        import config
        if not config._u0 or not config._r1():
            pytest.skip("Supabase não configurado")

        result = auth_manager.login("test@test.com", "password")

        assert "success" in result or "error" in result