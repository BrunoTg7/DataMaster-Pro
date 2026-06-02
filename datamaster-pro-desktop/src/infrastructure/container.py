"""
Dependency Injection Container - Inversão de controle
Conecta interfaces do domínio com implementações da infraestrutura.
"""
import threading
from typing import Optional

from src.domain.interfaces import (
    IUserRepository, ITaskRepository, IExecutionRepository,
    ISyncQueue, ISyncProvider, ICacheProvider, IEventBus,
)


class Container:
    """Container de dependências (Singleton thread-safe)."""

    _instance: Optional["Container"] = None
    _lock = threading.Lock()

    def __init__(self):
        # Repositories
        self._user_repo: Optional[IUserRepository] = None
        self._task_repo: Optional[ITaskRepository] = None
        self._execution_repo: Optional[IExecutionRepository] = None

        # Infrastructure
        self._sync_queue: Optional[ISyncQueue] = None
        self._sync_provider: Optional[ISyncProvider] = None
        self._cache: Optional[ICacheProvider] = None
        self._event_bus: Optional[IEventBus] = None

    @classmethod
    def get_instance(cls) -> "Container":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset para testes."""
        with cls._lock:
            cls._instance = None

    @property
    def user_repo(self) -> IUserRepository:
        if self._user_repo is None:
            from src.infrastructure.adapters import SQLiteUserRepository
            self._user_repo = SQLiteUserRepository()
        return self._user_repo

    @property
    def task_repo(self) -> ITaskRepository:
        if self._task_repo is None:
            from src.infrastructure.adapters import SQLiteTaskRepository
            self._task_repo = SQLiteTaskRepository()
        return self._task_repo

    @property
    def execution_repo(self) -> IExecutionRepository:
        if self._execution_repo is None:
            from src.infrastructure.adapters import SQLiteExecutionRepository
            self._execution_repo = SQLiteExecutionRepository()
        return self._execution_repo

    @property
    def sync_queue(self) -> ISyncQueue:
        if self._sync_queue is None:
            from src.infrastructure.adapters import SQLiteSyncQueue
            self._sync_queue = SQLiteSyncQueue()
        return self._sync_queue

    @property
    def sync_provider(self) -> ISyncProvider:
        if self._sync_provider is None:
            from src.infrastructure.adapters import SupabaseSyncProvider
            self._sync_provider = SupabaseSyncProvider()
        return self._sync_provider

    @property
    def cache(self) -> ICacheProvider:
        if self._cache is None:
            from src.infrastructure.adapters import MemoryCacheAdapter
            self._cache = MemoryCacheAdapter()
        return self._cache

    @property
    def event_bus(self) -> IEventBus:
        if self._event_bus is None:
            from src.infrastructure.adapters import EventBusAdapter
            self._event_bus = EventBusAdapter()
        return self._event_bus

    # ── Test injection ────────────────────────────────────────────────────

    def set_user_repo(self, repo: IUserRepository):
        self._user_repo = repo

    def set_task_repo(self, repo: ITaskRepository):
        self._task_repo = repo

    def set_execution_repo(self, repo: IExecutionRepository):
        self._execution_repo = repo

    def set_cache(self, cache: ICacheProvider):
        self._cache = cache

    def set_event_bus(self, bus: IEventBus):
        self._event_bus = bus
