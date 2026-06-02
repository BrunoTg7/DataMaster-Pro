"""
ToolService - Serviço de execução de ferramentas
Encapsula TaskExecutor para operações de criação, progresso e consulta de tarefas.
"""
import logging
from typing import Optional, Dict, List, Callable
from src.core.apm import PerformanceMonitor

log = logging.getLogger(__name__)


class ToolService:
    """Serviço que encapsula operações de execução de ferramentas."""

    def __init__(self):
        from src.core.tasks.task_executor import task_executor
        from src.core.memory_cache import get_cache
        self._executor = task_executor
        self._cache = get_cache()
        self._apm = PerformanceMonitor.get_instance()

    def submit(
        self,
        tool_name: str,
        tool_display_name: str,
        execute_func: Callable[[], dict],
        on_complete: Callable[[dict], None] = None,
        user_id: str = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """Submete uma execução arbitrária em background."""
        span = self._apm.start("tool_submit", {"tool": tool_name})
        try:
            result = self._executor.submit(
                tool_name, tool_display_name, execute_func, on_complete, user_id
            )
            self._apm.end(span, "ok")
            return result
        except Exception as e:
            self._apm.end(span, "error")
            raise

    def create_task(
        self,
        tool_name: str,
        input_params: dict,
        progress_callback: Callable = None,
        log_callback: Callable = None,
        auto_execute: bool = False,
        tool_display_name: str = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """Cria uma tarefa vinculada a uma ferramenta registrada."""
        span = self._apm.start("tool_create_task", {"tool": tool_name})
        try:
            result = self._executor.create_task(
                tool_name, input_params,
                progress_callback=progress_callback,
                log_callback=log_callback,
                auto_execute=auto_execute,
                tool_display_name=tool_display_name,
            )
            self._apm.end(span, "ok")
            return result
        except Exception as e:
            self._apm.end(span, "error")
            raise

    def update_progress(self, task_id: str, percent: int, message: str = ""):
        self._executor.update_progress(task_id, percent, message)

    def add_log(self, task_id: str, message: str):
        self._executor.add_log(task_id, message)

    def complete_task(self, task_id: str, output_path: str = "", rows: int = 0, hours: float = 0):
        self._executor.complete_task(task_id, output_path, rows, hours)

    def fail_task(self, task_id: str, error: str):
        self._executor.fail_task(task_id, error)

    def cancel_task(self, task_id: str) -> bool:
        return self._executor.cancel_task(task_id)

    def is_cancelled(self, task_id: str) -> bool:
        return self._executor.is_cancelled(task_id)

    def get_tasks(self, status_filter: str = None) -> List[dict]:
        return self._executor.get_tasks(status_filter)

    def get_task(self, task_id: str) -> Optional[dict]:
        return self._executor.get_task(task_id)

    def get_active_tasks(self) -> List[dict]:
        return self._executor.get_active_tasks()

    def get_running_count(self) -> int:
        return self._executor.get_running_count()

    def get_last_task_by_tool(self, tool_key: str) -> Optional[dict]:
        """Retorna a última tarefa de uma ferramenta (com cache)."""
        cache_key = f"last_task:{tool_key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        from src.core.storage.storage_manager import StorageManager
        storage = StorageManager()
        result = storage.get_last_task_by_tool(tool_key)
        if result:
            self._cache.set(cache_key, result, ttl=10)
        return result

    def register_tool(self, tool_name: str, tool_class: type):
        """Registra uma ferramenta no executor."""
        self._executor.register_tool(tool_name, tool_class)

    def recover_interrupted_tasks(self):
        self._executor.recover_interrupted_tasks()

    def invalidate_last_task_cache(self, tool_key: str = None):
        """Invalida cache de última tarefa."""
        if tool_key:
            self._cache.delete(f"last_task:{tool_key}")
        else:
            self._cache.clear(prefix="last_task:")

    @property
    def storage(self):
        return self._executor.storage

    @storage.setter
    def storage(self, value):
        self._executor.storage = value
