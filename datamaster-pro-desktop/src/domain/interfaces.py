"""
Domain Interfaces (Ports) - Contratos que a infraestrutura deve implementar
Estas são as "portas" da Clean Architecture. O domínio define O QUE,
a infraestrutura define COMO.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from src.domain.entities import (
    User, Task, Execution, TaskStatus, SyncStatus, SyncQueueItem
)


class IUserRepository(ABC):
    """Porta para persistência de usuários."""

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        ...

    @abstractmethod
    def save_user(self, user: User) -> None:
        ...

    @abstractmethod
    def get_session(self) -> Optional[Dict]:
        ...

    @abstractmethod
    def save_session(self, session_data: Dict) -> None:
        ...

    @abstractmethod
    def clear_session(self) -> None:
        ...

    @abstractmethod
    def get_token(self) -> Optional[str]:
        ...


class ITaskRepository(ABC):
    """Porta para persistência de tarefas."""

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Dict]:
        ...

    @abstractmethod
    def save_task(self, task_data: Dict) -> None:
        ...

    @abstractmethod
    def update_task(self, task_id: str, data: Dict) -> None:
        ...

    @abstractmethod
    def delete_task(self, task_id: str) -> None:
        ...

    @abstractmethod
    def get_all_tasks(self, status_filter: str = None, limit: int = 100) -> List[Dict]:
        ...

    @abstractmethod
    def get_last_task_by_tool(self, tool_name: str) -> Optional[Dict]:
        ...

    @abstractmethod
    def get_running_task_by_tool(self, tool_name: str) -> Optional[Dict]:
        ...


class IExecutionRepository(ABC):
    """Porta para persistência de execuções."""

    @abstractmethod
    def save_execution(self, execution: Execution) -> None:
        ...

    @abstractmethod
    def get_executions(self, user_id: str, limit: int = 100) -> List[Dict]:
        ...

    @abstractmethod
    def replace_user_executions(self, user_id: str, records: List[Dict]) -> None:
        ...


class ISyncQueue(ABC):
    """Porta para fila de sincronização."""

    @abstractmethod
    def add(self, operation: str, table: str, data: Dict) -> int:
        ...

    @abstractmethod
    def get_pending(self, limit: int = 100) -> List[SyncQueueItem]:
        ...

    @abstractmethod
    def mark_synced(self, item_id: int) -> None:
        ...

    @abstractmethod
    def mark_failed(self, item_id: int) -> None:
        ...

    @abstractmethod
    def cleanup(self) -> None:
        ...


class ISyncProvider(ABC):
    """Porta para provedor de sincronização (Supabase, etc)."""

    @abstractmethod
    def upload(self, table: str, data: Dict) -> bool:
        ...

    @abstractmethod
    def download(self, table: str, user_id: str, limit: int = 2000) -> List[Dict]:
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        ...


class IToolExecutor(ABC):
    """Porta para execução de ferramentas."""

    @abstractmethod
    def execute(self, tool_name: str, params: Dict) -> Dict:
        ...

    @abstractmethod
    def get_status(self, task_id: str) -> Optional[Task]:
        ...

    @abstractmethod
    def cancel(self, task_id: str) -> bool:
        ...


class ICacheProvider(ABC):
    """Porta para cache."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: float = 300) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def clear(self, prefix: str = "") -> None:
        ...


class IEventBus(ABC):
    """Porta para eventos (desacoplamento entre módulos)."""

    @abstractmethod
    def publish(self, event: str, data: Any = None) -> None:
        ...

    @abstractmethod
    def subscribe(self, event: str, callback) -> None:
        ...

    @abstractmethod
    def unsubscribe(self, event: str, callback) -> None:
        ...
