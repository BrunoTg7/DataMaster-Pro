import pytest
import os
import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta

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


@pytest.fixture
def sync_manager(tmp_db, monkeypatch):
    """Create a SyncManager with mocked network."""
    monkeypatch.setattr("src.utils.network.check_internet_connection", lambda: True)

    from src.core.sync.sync_manager import SyncManager
    sm = SyncManager(tmp_db)
    return sm


class TestSyncQueueOperations:

    def test_add_to_queue(self, sync_manager):
        data = {"usuario_id": "user-1", "tool_name": "consolidador", "created_at": "2026-01-01"}
        queue_id = sync_manager.add_to_queue("insert", "execucoes", data)
        assert queue_id > 0

    def test_get_pending_items(self, sync_manager):
        for i in range(3):
            sync_manager.add_to_queue("insert", "execucoes", {"usuario_id": "u1", "created_at": f"2026-01-0{i+1}"})

        pending = sync_manager.get_pending_items()
        assert len(pending) == 3

    def test_get_pending_items_with_limit(self, sync_manager):
        for i in range(5):
            sync_manager.add_to_queue("insert", "execucoes", {"usuario_id": "u1"})

        pending = sync_manager.get_pending_items(limit=2)
        assert len(pending) == 2

    def test_mark_synced(self, sync_manager):
        qid = sync_manager.add_to_queue("insert", "execucoes", {"usuario_id": "u1"})
        sync_manager.mark_synced(qid)

        pending = sync_manager.get_pending_items()
        assert len(pending) == 0

    def test_mark_failed_increments_retry(self, sync_manager):
        qid = sync_manager.add_to_queue("insert", "execucoes", {"usuario_id": "u1"})
        sync_manager.mark_failed(qid)

        conn = sqlite3.connect(sync_manager.storage.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT retry_count FROM sync_queue WHERE id = ?", (qid,))
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 1

    def test_mark_failed_excludes_after_3_retries(self, sync_manager):
        qid = sync_manager.add_to_queue("insert", "execucoes", {"usuario_id": "u1"})
        for _ in range(3):
            sync_manager.mark_failed(qid)

        pending = sync_manager.get_pending_items()
        assert len(pending) == 0

    def test_get_queue_stats(self, sync_manager):
        sync_manager.add_to_queue("insert", "execucoes", {"usuario_id": "u1"})
        qid2 = sync_manager.add_to_queue("insert", "execucoes", {"usuario_id": "u1"})
        sync_manager.mark_synced(qid2)

        stats = sync_manager.get_queue_stats()
        assert stats["pending"] == 1
        assert stats["synced"] == 1

    def test_add_to_queue_extracts_usuario_id(self, sync_manager):
        data = {"user_id": "user-from-data", "created_at": "2026-01-01"}
        qid = sync_manager.add_to_queue("insert", "execucoes", data)

        conn = sqlite3.connect(sync_manager.storage.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT usuario_id FROM sync_queue WHERE id = ?", (qid,))
        uid = cursor.fetchone()[0]
        conn.close()
        assert uid == "user-from-data"


class TestSyncManagerState:

    def test_initial_state(self, sync_manager):
        assert sync_manager.is_syncing is False
        assert sync_manager.last_sync is None
        assert sync_manager._c is None

    def test_set_on_sync_complete(self, sync_manager):
        callback = lambda: None
        sync_manager.set_on_sync_complete(callback)
        assert sync_manager._on_sync_complete is callback


class TestSyncNowWithMock:

    @patch("src.core.sync.sync_manager.SyncManager._get_client")
    @patch("src.core.sync.sync_manager.SyncManager.check_connection")
    def test_sync_now_skips_if_already_syncing(self, mock_check, mock_get_client, sync_manager):
        mock_check.return_value = True
        sync_manager.is_syncing = True

        result = sync_manager.sync_now()
        assert result["success"] is False
        assert "andamento" in result["error"]

    @patch("src.core.sync.sync_manager.SyncManager.check_connection")
    def test_sync_now_skips_if_no_connection(self, mock_check, sync_manager):
        mock_check.return_value = False

        result = sync_manager.sync_now()
        assert result["success"] is False
        assert result["offline"] is True

    @patch("src.core.sync.sync_manager.SyncManager._get_client")
    @patch("src.core.sync.sync_manager.SyncManager.check_connection")
    def test_sync_now_skips_if_no_pending(self, mock_check, mock_get_client, sync_manager):
        mock_check.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user = MagicMock()
        mock_client.auth.get_user.return_value = mock_user

        result = sync_manager.sync_now()
        assert result.get("synced", 0) == 0 or result.get("success") is False


class TestSyncManagerQueueTable:

    def test_queue_table_created(self, sync_manager):
        conn = sqlite3.connect(sync_manager.storage.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_queue'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_metadata_table_created(self, sync_manager):
        conn = sqlite3.connect(sync_manager.storage.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_metadata'")
        assert cursor.fetchone() is not None
        conn.close()
