"""
GlobalExecutor - Motor de execução global paralelo
Gerencia até 2 tarefas simultâneas em threads separadas
Tarefas CONTINUAM rodando mesmo quando o usuário navega entre páginas
"""
import uuid
import threading
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, List, Any
import sys
import os

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.storage.storage_manager import StorageManager


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GlobalTask:
    def __init__(self, task_id: str, tool_name: str, tool_display_name: str, user_id: str = None):
        self.id = task_id
        self.tool_name = tool_name
        self.tool_display_name = tool_display_name
        self.status = TaskStatus.PENDING
        self.progress_percent = 0
        self.progress_message = "Aguardando..."
        self.error_message = ""
        self.rows_processed = 0
        self.output_path = ""
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.user_id = user_id or ""
        self.log_messages: List[str] = []
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None


class GlobalExecutor:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._tasks: Dict[str, GlobalTask] = {}
        self._task_lock = threading.Lock()
        self._storage = StorageManager()
        self._new_task_callbacks: list = []
        self._initialized = True

    def on_new_task(self, callback):
        """Registra callback chamado quando uma nova task é criada"""
        self._new_task_callbacks.append(callback)

    def _notify_new_task(self):
        """Notifica listeners sobre nova task"""
        for cb in self._new_task_callbacks:
            try:
                cb()
            except Exception as e:
                logger.exception(f"Erro no callback de notificação")

    @property
    def max_concurrent(self) -> int:
        session = self._storage.get_saved_session()
        return 2 if session and session.get("plan") == "pro" else 1

    def submit(
        self,
        tool_name: str,
        tool_display_name: str,
        execute_func: Callable[[], dict],
        on_complete: Callable[[dict], None] = None,
        user_id: str = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Submete uma função para execução em background thread.
        A thread roda independente de páginas - sobrevive à navegação.
        execute_func: função que executa o trabalho (roda em thread separada)
        on_complete: callback chamado na thread da tarefa com o resultado
        Retorna (task_id, error_message)
        """
        with self._task_lock:
            running = [
                t
                for t in self._tasks.values()
                if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
            ]
            if len(running) >= self.max_concurrent:
                return None, f"Limite de {self.max_concurrent} tarefa(s) simultânea(s) atingido"

            same_tool = [t for t in running if t.tool_name == tool_name]
            if same_tool:
                return None, f"Uma tarefa de {tool_display_name} já está em execução"

            task_id = str(uuid.uuid4())
            task = GlobalTask(task_id, tool_name, tool_display_name, user_id)
            self._tasks[task_id] = task
            self._save_to_storage(task)

        self._notify_new_task()

        def run():
            try:
                with self._task_lock:
                    task.status = TaskStatus.RUNNING
                    task.progress_message = "Executando..."
                    self._save_to_storage(task)

                result = execute_func()

                if self.is_cancelled(task_id):
                    return

                with self._task_lock:
                    task.status = TaskStatus.COMPLETED
                    task.progress_percent = 100
                    task.progress_message = "Concluído"
                    task.completed_at = datetime.now().isoformat()
                    if isinstance(result, dict):
                        task.rows_processed = result.get("rows_processed", 0)
                        task.output_path = result.get("output_path", "")
                    self._save_to_storage(task)

                if on_complete:
                    on_complete(result)

            except Exception as e:
                if self.is_cancelled(task_id):
                    return
                with self._task_lock:
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                    task.progress_message = f"Erro: {e}"
                    task.completed_at = datetime.now().isoformat()
                    self._save_to_storage(task)
                if on_complete:
                    on_complete({"success": False, "error": str(e)})

        task._thread = threading.Thread(target=run, daemon=True)
        task._thread.start()

        return task_id, None

    def cancel_task(self, task_id: str) -> bool:
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
                return False
            task._cancel_event.set()
            task.status = TaskStatus.CANCELLED
            task.progress_message = "Cancelado"
            task.completed_at = datetime.now().isoformat()
            self._save_to_storage(task)
            return True

    def is_cancelled(self, task_id: str) -> bool:
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return True
            return task._cancel_event.is_set()

    def update_progress(self, task_id: str, percent: int, message: str = ""):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            if task._cancel_event.is_set():
                return
            task.status = TaskStatus.RUNNING
            task.progress_percent = min(100, max(0, percent))
            if message:
                task.progress_message = message
            self._save_to_storage(task)

    def add_log(self, task_id: str, message: str):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            ts = datetime.now().strftime("%H:%M:%S")
            task.log_messages.append(f"[{ts}] {message}")
            task.log_messages = task.log_messages[-100:]

    def get_tasks(self) -> List[dict]:
        with self._task_lock:
            return [self._task_to_dict(t) for t in self._tasks.values()]

    def get_active_tasks(self) -> List[dict]:
        with self._task_lock:
            return [
                self._task_to_dict(t)
                for t in self._tasks.values()
                if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED)
            ]

    def get_task(self, task_id: str) -> Optional[dict]:
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            return self._task_to_dict(task)

    def get_running_count(self) -> int:
        with self._task_lock:
            return len(
                [
                    t
                    for t in self._tasks.values()
                    if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
                ]
            )

    def recover_interrupted_tasks(self):
        """Marca tarefas que estavam rodando como finalizadas"""
        with self._task_lock:
            for task in self._tasks.values():
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.CANCELLED
                    task.progress_message = "Interrompido - aplicação fechada"
                    task.completed_at = datetime.now().isoformat()
                    self._save_to_storage(task)

    def _task_to_dict(self, task: GlobalTask) -> dict:
        return {
            "id": task.id,
            "tool_name": task.tool_name,
            "tool_display_name": task.tool_display_name,
            "status": task.status,
            "progress_percent": task.progress_percent,
            "progress_message": task.progress_message,
            "error_message": task.error_message,
            "rows_processed": task.rows_processed,
            "output_path": task.output_path,
            "created_at": task.created_at,
            "completed_at": task.completed_at or "",
            "user_id": task.user_id,
            "log_text": "\n".join(task.log_messages[-20:]),
            "input_params": "{}",
            "hours_saved": 0,
        }

    def _save_to_storage(self, task: GlobalTask):
        try:
            d = self._task_to_dict(task)
            storage_data = {
                "id": task.id,
                "tool_name": d["tool_name"],
                "tool_display_name": d.get("tool_display_name", d["tool_name"]),
                "status": d["status"],
                "progress_percent": d["progress_percent"],
                "progress_message": d["progress_message"],
                "output_path": d["output_path"],
                "log_text": d["log_text"],
                "rows_processed": d["rows_processed"],
                "created_at": d["created_at"],
                "user_id": d["user_id"] or "",
                "error_message": d["error_message"],
                "input_params": "{}",
                "hours_saved": 0,
            }
            existing = self._storage.get_task(task.id)
            if existing:
                self._storage.update_task(task.id, storage_data)
            else:
                self._storage.save_task(storage_data)
        except Exception as e:
            logger.error(f"Erro ao persistir tarefa {task.id}: {e}")


global_executor = GlobalExecutor()
