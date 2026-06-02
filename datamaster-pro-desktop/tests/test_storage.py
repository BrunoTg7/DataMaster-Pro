import pytest
import os
import sys
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    """Create a StorageManager with a temporary database."""
    test_db = tmp_path / "test.db"

    monkeypatch.setattr("config.DB_PATH", str(test_db))
    monkeypatch.setattr("config.ENCRYPTION_KEY", "test-secret-key-for-testing-32c!")

    from src.core.storage.storage_manager import StorageManager
    sm = StorageManager()
    return sm


class TestStorageManagerInit:

    def test_creates_database_file(self, tmp_db):
        assert os.path.exists(tmp_db.db_path)

    def test_creates_required_tables(self, tmp_db):
        conn = sqlite3.connect(tmp_db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "users" in tables
        assert "executions" in tables
        assert "tasks" in tables
        assert "settings" in tables

    def test_creates_indices(self, tmp_db):
        conn = sqlite3.connect(tmp_db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "idx_executions_user" in indices
        assert "idx_tasks_status" in indices


class TestUserSession:

    def test_save_and_get_session(self, tmp_db):
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "plan": "pro",
            "expires_at": "2099-01-01",
            "created_at": "2026-01-01",
            "session_token": "tok_abc123",
            "refresh_token": "ref_xyz789",
            "theme": "dark",
            "notificacoes_email": True,
            "notificacoes_desktop": False,
        }
        tmp_db.save_user_session(user_data)
        session = tmp_db.get_saved_session()

        assert session is not None
        assert session["id"] == "user-123"
        assert session["email"] == "test@example.com"
        assert session["plan"] == "pro"
        assert session["session_token"] == "tok_abc123"
        assert session["refresh_token"] == "ref_xyz789"
        assert session["theme"] == "dark"
        assert session["notificacoes_email"] is True
        assert session["notificacoes_desktop"] is False

    def test_get_saved_session_empty(self, tmp_db):
        assert tmp_db.get_saved_session() is None

    def test_save_session_encrypts_tokens(self, tmp_db):
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "session_token": "plain_token",
            "refresh_token": "plain_refresh",
        }
        tmp_db.save_user_session(user_data)

        conn = sqlite3.connect(tmp_db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT session_token_encrypted, password_encrypted FROM users LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        assert row[0] != "plain_token"
        assert row[1] != "plain_refresh"
        assert len(row[0]) > 0
        assert len(row[1]) > 0

    def test_clear_session(self, tmp_db):
        user_data = {"id": "user-123", "email": "test@example.com"}
        tmp_db.save_user_session(user_data)
        assert tmp_db.get_saved_session() is not None

        tmp_db.clear_session()
        assert tmp_db.get_saved_session() is None

    def test_get_token(self, tmp_db):
        user_data = {
            "id": "user-123",
            "session_token": "my_token",
        }
        tmp_db.save_user_session(user_data)
        assert tmp_db.get_token() == "my_token"

    def test_get_token_no_session(self, tmp_db):
        assert tmp_db.get_token() is None

    def test_get_user_data(self, tmp_db):
        user_data = {"id": "user-456", "email": "a@b.com", "plan": "gratis"}
        tmp_db.save_user_session(user_data)
        data = tmp_db.get_user_data()
        assert data["id"] == "user-456"
        assert data["plan"] == "gratis"

    def test_get_stored_credentials(self, tmp_db):
        user_data = {
            "id": "user-123",
            "refresh_token": "my_refresh",
        }
        tmp_db.save_user_session(user_data)
        creds = tmp_db.get_stored_credentials()
        assert creds is not None
        assert creds["refresh_token"] == "my_refresh"

    def test_get_stored_credentials_no_refresh(self, tmp_db):
        user_data = {"id": "user-123"}
        tmp_db.save_user_session(user_data)
        assert tmp_db.get_stored_credentials() is None


class TestTheme:

    def test_save_and_get_theme(self, tmp_db):
        user_data = {"id": "user-123"}
        tmp_db.save_user_session(user_data)

        tmp_db.save_theme("light")
        assert tmp_db.get_theme() == "light"

    def test_get_theme_default(self, tmp_db):
        assert tmp_db.get_theme() == "system"

    def test_save_and_get_tool_theme(self, tmp_db):
        tmp_db.save_tool_theme("minerador", "dark")
        assert tmp_db.get_tool_theme("minerador") == "dark"

    def test_get_tool_theme_default(self, tmp_db):
        assert tmp_db.get_tool_theme("nonexistent") == "classic_blue"


class TestHistoryRetention:

    def test_save_and_get_retention(self, tmp_db):
        user_data = {"id": "user-123"}
        tmp_db.save_user_session(user_data)

        tmp_db.save_history_retention("30d")
        conn = sqlite3.connect(tmp_db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT history_retention FROM users LIMIT 1")
        val = cursor.fetchone()[0]
        conn.close()
        assert val == "30d"

    def test_get_retention_default(self, tmp_db):
        assert tmp_db.get_history_retention() == "15d"


class TestTasks:

    def test_save_and_get_task(self, tmp_db):
        task = {
            "id": "task-001",
            "tool_name": "consolidador",
            "tool_display_name": "Consolidador",
            "status": "running",
            "progress_percent": 50,
            "progress_message": "Processando...",
            "input_params": "{}",
            "output_path": "/tmp/out.xlsx",
            "log_text": "log",
            "rows_processed": 100,
            "hours_saved": 0.5,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "user_id": "user-123",
        }
        tmp_db.save_task(task)
        result = tmp_db.get_task("task-001")

        assert result is not None
        assert result["tool_name"] == "consolidador"
        assert result["status"] == "running"
        assert result["progress_percent"] == 50
        assert result["rows_processed"] == 100

    def test_get_task_not_found(self, tmp_db):
        assert tmp_db.get_task("nonexistent") is None

    def test_get_all_tasks(self, tmp_db):
        for i in range(5):
            tmp_db.save_task({"id": f"task-{i}", "tool_name": "tool", "status": "completed"})
        tasks = tmp_db.get_all_tasks()
        assert len(tasks) == 5

    def test_get_all_tasks_with_filter(self, tmp_db):
        tmp_db.save_task({"id": "t1", "tool_name": "tool", "status": "running"})
        tmp_db.save_task({"id": "t2", "tool_name": "tool", "status": "completed"})
        tmp_db.save_task({"id": "t3", "tool_name": "tool", "status": "running"})

        running = tmp_db.get_all_tasks(status_filter="running")
        assert len(running) == 2

    def test_get_active_tasks(self, tmp_db):
        tmp_db.save_task({"id": "t1", "tool_name": "tool", "status": "pending"})
        tmp_db.save_task({"id": "t2", "tool_name": "tool", "status": "running"})
        tmp_db.save_task({"id": "t3", "tool_name": "tool", "status": "completed"})

        active = tmp_db.get_active_tasks()
        assert len(active) == 2

    def test_update_task(self, tmp_db):
        tmp_db.save_task({"id": "t1", "tool_name": "tool", "status": "pending"})
        tmp_db.update_task("t1", {"status": "running", "progress_percent": 25})

        task = tmp_db.get_task("t1")
        assert task["status"] == "running"
        assert task["progress_percent"] == 25

    def test_update_task_ignores_invalid_columns(self, tmp_db):
        tmp_db.save_task({"id": "t1", "tool_name": "tool", "status": "pending"})
        tmp_db.update_task("t1", {"status": "running", "evil_column": "hack"})

        task = tmp_db.get_task("t1")
        assert task["status"] == "running"

    def test_delete_task(self, tmp_db):
        tmp_db.save_task({"id": "t1", "tool_name": "tool"})
        tmp_db.delete_task("t1")
        assert tmp_db.get_task("t1") is None

    def test_get_running_task_by_tool(self, tmp_db):
        tmp_db.save_task({"id": "t1", "tool_name": "minerador", "status": "running"})
        tmp_db.save_task({"id": "t2", "tool_name": "consolidador", "status": "running"})

        result = tmp_db.get_running_task_by_tool("minerador")
        assert result is not None
        assert result["id"] == "t1"

    def test_get_running_task_by_tool_none(self, tmp_db):
        assert tmp_db.get_running_task_by_tool("nonexistent") is None

    def test_get_last_task_by_tool(self, tmp_db):
        tmp_db.save_task({"id": "t1", "tool_name": "miner", "status": "completed", "created_at": "2026-01-01T10:00:00"})
        tmp_db.save_task({"id": "t2", "tool_name": "miner", "status": "running", "created_at": "2026-01-02T10:00:00"})

        result = tmp_db.get_last_task_by_tool("miner")
        assert result["id"] == "t2"

    def test_get_last_task_by_tool_exclude_failed(self, tmp_db):
        tmp_db.save_task({"id": "t1", "tool_name": "miner", "status": "failed"})
        tmp_db.save_task({"id": "t2", "tool_name": "miner", "status": "completed"})

        result = tmp_db.get_last_task_by_tool("miner", exclude_failed=True)
        assert result["id"] == "t2"

    def test_cleanup_old_tasks(self, tmp_db):
        from datetime import datetime, timedelta
        old = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")

        tmp_db.save_task({"id": "t1", "tool_name": "tool", "status": "completed", "updated_at": old})
        tmp_db.save_task({"id": "t2", "tool_name": "tool", "status": "running", "updated_at": old})

        tmp_db.cleanup_old_tasks(days=7)
        assert tmp_db.get_task("t1") is None
        assert tmp_db.get_task("t2") is not None


class TestExecutions:

    def test_save_and_get_executions(self, tmp_db):
        tmp_db.save_execution("user-1", "consolidador", ["in.xlsx"], "out.xlsx", 100, 0.5)
        tmp_db.save_execution("user-1", "minerador", ["urls.txt"], "result.csv", 50, 0.3)

        execs = tmp_db.get_executions("user-1")
        assert len(execs) == 2

    def test_get_executions_with_limit(self, tmp_db):
        for i in range(10):
            tmp_db.save_execution("user-1", "tool", [], "out", i, 0)

        execs = tmp_db.get_executions("user-1", limit=3)
        assert len(execs) == 3

    def test_get_executions_empty(self, tmp_db):
        assert tmp_db.get_executions("nonexistent") == []

    def test_replace_user_executions(self, tmp_db):
        tmp_db.save_execution("user-1", "tool1", [], "out1", 10, 0)
        tmp_db.save_execution("user-1", "tool2", [], "out2", 20, 0)

        new_records = [
            {"ferramenta": "tool3", "linhas_processadas": 30, "tempo_execucao_ms": 100, "created_at": "2026-01-01"},
            {"ferramenta": "tool4", "linhas_processadas": 40, "tempo_execucao_ms": 200, "created_at": "2026-01-02"},
        ]
        tmp_db.replace_user_executions("user-1", new_records)

        execs = tmp_db.get_executions("user-1")
        assert len(execs) == 2


class TestSafeDbDecorator:

    def test_propagates_integrity_error(self, tmp_db):
        from src.core.storage.storage_manager import IntegrityError
        tmp_db.save_task({"id": "dup-1", "tool_name": "tool"})
        with pytest.raises(IntegrityError):
            tmp_db.save_task({"id": "dup-1", "tool_name": "tool"})

    def test_returns_none_on_generic_error(self, tmp_db):
        result = tmp_db.get_task("")
        assert result is None


class TestCorruptedSession:

    def test_corrupted_session_returns_none(self, tmp_db, monkeypatch):
        user_data = {"id": "user-123", "session_token": "token"}
        tmp_db.save_user_session(user_data)

        original_decrypt = tmp_db._user._decrypt
        def failing_decrypt(x):
            raise Exception("decrypt failed")
        monkeypatch.setattr(tmp_db._user, "_decrypt", failing_decrypt)

        session = tmp_db.get_saved_session()
        assert session is None
