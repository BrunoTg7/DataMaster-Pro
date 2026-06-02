"""
Infrastructure Adapters - Implementações das interfaces do domínio
Usa o código existente (StorageManager, SyncManager, etc) como back-end.
"""
import json
import logging
from typing import Optional, List, Dict, Any

from src.domain.entities import (
    User, Task, Execution, SyncQueueItem, PlanType, SyncStatus
)
from src.domain.interfaces import (
    IUserRepository, ITaskRepository, IExecutionRepository,
    ISyncQueue, ISyncProvider, ICacheProvider, IEventBus,
)

log = logging.getLogger(__name__)


class SQLiteUserRepository(IUserRepository):
    """Adapta StorageManager para IUserRepository."""

    def __init__(self):
        from src.core.storage.storage_manager import StorageManager
        self._storage = StorageManager()

    def get_user(self, user_id: str) -> Optional[User]:
        session = self._storage.get_saved_session()
        if not session:
            return None
        return User(
            id=session.get("id", ""),
            email=session.get("email", ""),
            plan=PlanType(session.get("plan", "gratis")),
            data_expiracao=session.get("data_expiracao"),
            created_at=session.get("created_at"),
        )

    def save_user(self, user: User) -> None:
        self._storage.save_user_session({
            "id": user.id,
            "email": user.email,
            "plan": user.plan.value,
            "data_expiracao": user.data_expiracao,
        })

    def get_session(self) -> Optional[Dict]:
        return self._storage.get_saved_session()

    def save_session(self, session_data: Dict) -> None:
        self._storage.save_user_session(session_data)

    def clear_session(self) -> None:
        self._storage.clear_session()

    def get_token(self) -> Optional[str]:
        return self._storage.get_token()


class SQLiteTaskRepository(ITaskRepository):
    """Adapta StorageManager para ITaskRepository."""

    def __init__(self, db_path: str = None):
        from src.core.storage.task_storage import TaskStorage
        self._tasks = TaskStorage(db_path) if db_path else TaskStorage()

    def get_task(self, task_id: str) -> Optional[Dict]:
        return self._tasks.get_task(task_id)

    def save_task(self, task_data: Dict) -> None:
        self._tasks.save_task(task_data)

    def update_task(self, task_id: str, data: Dict) -> None:
        self._tasks.update_task(task_id, data)

    def delete_task(self, task_id: str) -> None:
        self._tasks.delete_task(task_id)

    def get_all_tasks(self, status_filter: str = None, limit: int = 100) -> List[Dict]:
        return self._tasks.get_all_tasks(status_filter=status_filter, limit=limit)

    def get_last_task_by_tool(self, tool_name: str) -> Optional[Dict]:
        return self._tasks.get_last_task_by_tool(tool_name)

    def get_running_task_by_tool(self, tool_name: str) -> Optional[Dict]:
        return self._tasks.get_running_task_by_tool(tool_name)


class SQLiteExecutionRepository(IExecutionRepository):
    """Adapta StorageManager para IExecutionRepository."""

    def __init__(self, db_path: str = None):
        from src.core.storage.execution_storage import ExecutionStorage
        self._executions = ExecutionStorage(db_path) if db_path else ExecutionStorage()

    def save_execution(self, execution: Execution) -> None:
        self._executions.save_execution(
            execution.user_id, execution.tool_name,
            json.loads(execution.input_files) if isinstance(execution.input_files, str) else execution.input_files,
            execution.output_path, execution.rows_processed, execution.hours_saved,
        )

    def get_executions(self, user_id: str, limit: int = 100) -> List[Dict]:
        return self._executions.get_executions(user_id, limit=limit)

    def replace_user_executions(self, user_id: str, records: List[Dict]) -> None:
        self._executions.replace_user_executions(user_id, records)


class SQLiteSyncQueue(ISyncQueue):
    """Adapta SyncManager para ISyncQueue."""

    def __init__(self):
        from src.core.storage.storage_manager import StorageManager
        from src.core.sync.sync_manager import SyncManager
        self._storage = StorageManager()
        self._sync = SyncManager(self._storage)

    def add(self, operation: str, table: str, data: Dict) -> int:
        return self._sync.add_to_queue(operation, table, data)

    def get_pending(self, limit: int = 100) -> List[SyncQueueItem]:
        items = self._sync.get_pending_items(limit)
        return [
            SyncQueueItem(
                id=i["id"],
                operation=i.get("operation", ""),
                table_name=i.get("table_name", ""),
                data_json=json.dumps(i.get("data", {})),
                usuario_id=i.get("usuario_id", ""),
                status=SyncStatus(i.get("status", "pending")),
                retry_count=i.get("retry_count", 0),
                created_at=i.get("created_at", ""),
            )
            for i in items
        ]

    def mark_synced(self, item_id: int) -> None:
        self._sync.mark_synced(item_id)

    def mark_failed(self, item_id: int) -> None:
        self._sync.mark_failed(item_id)

    def cleanup(self) -> None:
        self._sync._cleanup_queue()


class SupabaseSyncProvider(ISyncProvider):
    """Adapta Supabase client para ISyncProvider."""

    def __init__(self):
        self._client = None
        self._token = None

    def _get_client(self, token: str = None):
        from supabase import create_client
        import config
        if self._client is None or (token and token != self._token):
            self._client = create_client(config._u0, config._r1())
            self._token = token
            if token:
                self._client.postgrest.auth(token)
        return self._client

    def upload(self, table: str, data: Dict) -> bool:
        from src.core.services import get_user_service
        token = get_user_service().get_token()
        client = self._get_client(token)
        client.table(table).upsert(data).execute()
        return True

    def download(self, table: str, user_id: str, limit: int = 2000) -> List[Dict]:
        from src.core.services import get_user_service
        token = get_user_service().get_token()
        client = self._get_client(token)
        result = (
            client.table(table)
            .select("*")
            .eq("usuario_id" if table == "execucoes" else "user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def is_connected(self) -> bool:
        from src.utils.network import check_internet_connection
        return check_internet_connection()


class MemoryCacheAdapter(ICacheProvider):
    """Adapta MemoryCache para ICacheProvider."""

    def __init__(self):
        from src.core.memory_cache import get_cache
        self._cache = get_cache()

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: float = 300) -> None:
        self._cache.set(key, value, ttl)

    def delete(self, key: str) -> None:
        self._cache.delete(key)

    def clear(self, prefix: str = "") -> None:
        self._cache.clear(prefix)


class EventBusAdapter(IEventBus):
    """Implementação simples de evento bus em memória."""

    def __init__(self):
        self._subscribers: Dict[str, List] = {}

    def publish(self, event: str, data: Any = None) -> None:
        for callback in self._subscribers.get(event, []):
            try:
                callback(data)
            except Exception as e:
                log.error("EventBus error in '%s': %s", event, e)

    def subscribe(self, event: str, callback) -> None:
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback) -> None:
        if event in self._subscribers:
            self._subscribers[event] = [
                cb for cb in self._subscribers[event] if cb != callback
            ]
