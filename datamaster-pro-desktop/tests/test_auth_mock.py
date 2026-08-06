import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.auth.auth_manager import AuthManager


@pytest.fixture
def auth_manager():
    return AuthManager()


class TestAuthManagerInit:

    def test_initial_state(self, auth_manager):
        assert auth_manager.current_user is None
        assert auth_manager._session_token is None
        assert auth_manager._stored_credentials is None


class TestSessionManagement:

    def test_get_current_user_none(self, auth_manager):
        assert auth_manager.get_current_user() is None

    def test_set_current_user(self, auth_manager):
        user_data = {"id": "u1", "email": "test@test.com", "plan": "pro"}
        auth_manager.set_current_user(user_data)
        assert auth_manager.get_current_user() == user_data

    def test_logout_clears_session(self, auth_manager):
        auth_manager.current_user = {"email": "test@test.com"}
        auth_manager._session_token = "fake_token"
        auth_manager._stored_credentials = {"refresh_token": "refresh"}

        auth_manager.logout()

        assert auth_manager.current_user is None
        assert auth_manager._session_token is None


class TestSessionValidity:

    def test_is_session_valid_false_no_user(self, auth_manager):
        assert auth_manager.is_session_valid() is False

    def test_is_session_valid_not_expired(self, auth_manager):
        auth_manager.current_user = {
            "email": "test@test.com",
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }
        assert auth_manager.is_session_valid() is True

    def test_is_session_valid_expired(self, auth_manager):
        auth_manager.current_user = {
            "email": "test@test.com",
            "expires_at": (datetime.now() - timedelta(days=1)).isoformat()
        }
        assert auth_manager.is_session_valid() is False

    def test_is_session_valid_no_expiry(self, auth_manager):
        auth_manager.current_user = {"email": "test@test.com"}
        assert auth_manager.is_session_valid() is True

    def test_is_session_valid_invalid_format(self, auth_manager):
        auth_manager.current_user = {
            "email": "test@test.com",
            "expires_at": "not-a-date"
        }
        assert auth_manager.is_session_valid() is False


class TestPlanExpired:

    def test_is_plan_expired_no_user(self, auth_manager):
        assert auth_manager.is_plan_expired() is True

    def test_is_plan_expired_gratis_never_expires(self, auth_manager):
        auth_manager.current_user = {"plan": "gratis"}
        assert auth_manager.is_plan_expired() is False

    def test_is_plan_expired_no_expiry_date(self, auth_manager):
        auth_manager.current_user = {"plan": "pro", "data_expiracao": None}
        assert auth_manager.is_plan_expired() is False

    def test_is_plan_expired_not_expired(self, auth_manager):
        auth_manager.current_user = {
            "plan": "pro",
            "data_expiracao": (datetime.now() + timedelta(days=30)).isoformat()
        }
        assert auth_manager.is_plan_expired() is False

    def test_is_plan_expired_expired(self, auth_manager):
        auth_manager.current_user = {
            "plan": "pro",
            "data_expiracao": (datetime.now() - timedelta(days=1)).isoformat()
        }
        assert auth_manager.is_plan_expired() is True

    def test_is_plan_expired_invalid_date(self, auth_manager):
        auth_manager.current_user = {"plan": "pro", "data_expiracao": "invalid"}
        assert auth_manager.is_plan_expired() is False


class TestLoginWithSupabaseMock:

    @patch("supabase.create_client")
    def test_login_success(self, mock_create, auth_manager):
        mock_client = MagicMock()
        mock_create.return_value = mock_client

        mock_response = MagicMock()
        mock_response.user.id = "user-123"
        mock_response.user.email = "test@test.com"
        mock_response.session.access_token = "access_tok"
        mock_response.session.refresh_token = "refresh_tok"
        mock_client.auth.sign_in_with_password.return_value = mock_response

        mock_profile = MagicMock()
        mock_profile.data = [{"plano_tipo": "pro", "nome": "Test"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_profile

        result = auth_manager.login("test@test.com", "password")

        assert result["success"] is True
        assert result["user"]["id"] == "user-123"
        assert auth_manager._session_token == "access_tok"

    @patch("supabase.create_client")
    def test_login_failure(self, mock_create, auth_manager):
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        mock_client.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")

        result = auth_manager.login("test@test.com", "wrong")

        assert result["success"] is False
        assert "Login falhou" in result["error"]

    @patch("supabase.create_client")
    def test_login_with_session_success(self, mock_create, auth_manager):
        mock_client = MagicMock()
        mock_create.return_value = mock_client

        mock_response = MagicMock()
        mock_response.user.id = "user-123"
        mock_response.user.email = "test@test.com"
        mock_response.session.access_token = "new_access"
        mock_response.session.refresh_token = "new_refresh"
        mock_client.auth.refresh_session.return_value = mock_response

        mock_profile = MagicMock()
        mock_profile.data = [{"plano_tipo": "gratis"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_profile

        result = auth_manager.login_with_session("old_refresh_token")

        assert result["success"] is True
        assert auth_manager._session_token == "new_access"

    def test_login_with_session_no_token(self, auth_manager):
        result = auth_manager.login_with_session("")
        assert result["success"] is False
        assert "No session refresh token" in result["error"]

    def test_login_with_stored_credentials_none(self, auth_manager):
        result = auth_manager.login_with_stored_credentials()
        assert result["success"] is False
        assert "No stored credentials" in result["error"]

    @patch("supabase.create_client")
    def test_login_with_stored_credentials(self, mock_create, auth_manager):
        auth_manager._stored_credentials = {"refresh_token": "stored_refresh"}

        mock_client = MagicMock()
        mock_create.return_value = mock_client

        mock_response = MagicMock()
        mock_response.user.id = "user-123"
        mock_response.user.email = "test@test.com"
        mock_response.session.access_token = "renewed_access"
        mock_response.session.refresh_token = "renewed_refresh"
        mock_client.auth.refresh_session.return_value = mock_response

        mock_profile = MagicMock()
        mock_profile.data = [{"plano_tipo": "pro"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_profile

        result = auth_manager.login_with_stored_credentials()

        assert result["success"] is True
        mock_client.auth.refresh_session.assert_called_once_with("stored_refresh")
