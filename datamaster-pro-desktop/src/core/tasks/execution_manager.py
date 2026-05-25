"""
ExecutionManager - Gerenciador profissional de execuções paralelas
Permite executar até 2 tarefas simultâneas de ferramentas DIFERENTES
Com persistência de estado entre navegações e recuperação de tarefas interrompidas
"""
import uuid
import json
import threading
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List, Callable
from pathlib import Path
import os
import sys

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.storage.storage_manager import StorageManager


class ExecutionState:
    """Estados de execução"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class ExecutionTask:
    """Modelo de tarefa de execução"""
    def __init__(
        self,
        task_id: str,
        tool_name: str,
        tool_display_name: str,
        status: str = ExecutionState.PENDING,
        progress_percent: int = 0,
        progress_message: str = "",
        error_message: str = "",
        started_at: str = None,
        completed_at: str = None,
        user_id: str = None
    ):
        self.id = task_id
        self.tool_name = tool_name
        self.tool_display_name = tool_display_name
        self.status = status
        self.progress_percent = progress_percent
        self.progress_message = progress_message
        self.error_message = error_message
        self.started_at = started_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.user_id = user_id
        self.log_messages: List[str] = []
        self.result_data: Dict = {}

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "tool_display_name": self.tool_display_name,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "progress_message": self.progress_message,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "user_id": self.user_id,
            "log_messages": self.log_messages[-50:],  # Últimas 50 mensagens
            "result_data": self.result_data
        }

    @staticmethod
    def from_dict(data: Dict) -> "ExecutionTask":
        task = ExecutionTask(
            task_id=data["id"],
            tool_name=data["tool_name"],
            tool_display_name=data.get("tool_display_name", data["tool_name"]),
            status=data.get("status", ExecutionState.PENDING),
            progress_percent=data.get("progress_percent", 0),
            progress_message=data.get("progress_message", ""),
            error_message=data.get("error_message", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            user_id=data.get("user_id")
        )
        task.log_messages = data.get("log_messages", [])
        task.result_data = data.get("result_data", {})
        return task


class ExecutionManager:
    """Gerenciador central de execuções paralelas com persistência"""
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, storage: StorageManager = None):
        if self._initialized:
            return

        self.storage = storage or StorageManager()
        self._tasks: Dict[str, ExecutionTask] = {}
        self._callbacks: Dict[str, Dict[str, Callable]] = {}
        self._state_file = Path(config.BASE_DIR) / ".execution_state.json"
        self._running_threads: Dict[str, threading.Thread] = {}
        self._lock = threading.RLock()
        self._state_update_callbacks: List[Callable] = []
        self.max_concurrent = 2

        self._load_persisted_state()
        self._initialized = True

    def register_state_change_callback(self, callback: Callable):
        """Registra callback para mudanças no estado de execução"""
        self._state_update_callbacks.append(callback)

    def _notify_state_change(self):
        """Notifica todos os listeners sobre mudança de estado"""
        with self._lock:
            active = self.get_active_tasks()
        for callback in self._state_update_callbacks:
            try:
                callback(active)
            except Exception as e:
                logger.exception(f"Erro ao salvar estado persistido")
            raise

    def _load_persisted_state(self):
        """Carrega estado persistido do arquivo JSON"""
        try:
            if not self._state_file.exists():
                return

            with open(self._state_file, "r") as f:
                state = json.load(f)

            # Recuperar tarefas
            for task_data in state.get("tasks", []):
                task = ExecutionTask.from_dict(task_data)
                self._tasks[task.id] = task

                # Se estava em execução ou pendente, marcar como interrompida (não failed)
                if task.status in (ExecutionState.RUNNING, ExecutionState.PENDING):
                    task.status = "interrupted"
                    task.error_message = "Aplicação foi fechada durante a execução - tarefa interrompida"

            # Limpar tarefas muito antigas da memória (>7 dias)
            self.clear_old_tasks(days=7)
            logger.info(f"Carregadas {len(self._tasks)} tarefas persistidas")
        except Exception as e:
            logger.error(f"Erro ao carregar estado persistido: {e}")

    def create_task(
        self,
        tool_name: str,
        tool_display_name: str,
        user_id: str = None,
        progress_callback: Callable = None,
        log_callback: Callable = None
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Cria uma nova tarefa de execução
        Retorna: (task_id, error_message)
        """
        with self._lock:
            # Verificar limite de tarefas simultâneas
            running_count = len(self.get_running_tasks())
            if running_count >= self.max_concurrent:
                return None, f"Limite de {self.max_concurrent} tarefas simultâneas atingido"

            # Verificar se há outra ferramenta DO MESMO TIPO em execução
            for task in self.get_running_tasks():
                if task.tool_name == tool_name:
                    return None, f"Uma tarefa de {tool_display_name} já está em execução"

            # Criar nova tarefa
            task_id = str(uuid.uuid4())
            task = ExecutionTask(
                task_id=task_id,
                tool_name=tool_name,
                tool_display_name=tool_display_name,
                user_id=user_id,
                status=ExecutionState.PENDING
            )

            self._tasks[task_id] = task
            self._callbacks[task_id] = {
                "progress": progress_callback,
                "log": log_callback
            }

            self._save_persisted_state()
            self._notify_state_change()

            return task_id, None

    def get_task(self, task_id: str) -> Optional[ExecutionTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def get_running_tasks(self) -> List[ExecutionTask]:
        with self._lock:
            return [
                t for t in self._tasks.values()
                if t.status in [ExecutionState.PENDING, ExecutionState.RUNNING]
            ]

    def get_active_tasks(self) -> List[ExecutionTask]:
        with self._lock:
            return [
                t for t in self._tasks.values()
                if t.status != ExecutionState.CANCELLED
            ]

    def get_all_tasks(self) -> List[ExecutionTask]:
        with self._lock:
            return list(self._tasks.values())

    def update_progress(self, task_id: str, percent: int, message: str = ""):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.status = ExecutionState.RUNNING
            task.progress_percent = min(100, max(0, percent))
            if message:
                task.progress_message = message
            self._save_persisted_state()
            self._notify_state_change()
            callbacks = dict(self._callbacks.get(task_id, {}))

        if callbacks.get("progress"):
            try:
                callbacks["progress"](percent, message)
            except Exception:
                pass

    def add_log(self, task_id: str, message: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            task.log_messages = task.log_messages[-100:]
            self._save_persisted_state()
            callbacks = dict(self._callbacks.get(task_id, {}))

        if callbacks.get("log"):
            try:
                callbacks["log"](message)
            except Exception:
                pass

    def complete_task(self, task_id: str, result_data: Dict = None):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.status = ExecutionState.COMPLETED
            task.progress_percent = 100
            task.progress_message = "Concluído"
            task.completed_at = datetime.now().isoformat()
            if result_data:
                task.result_data = result_data
            self._save_persisted_state()
            self._notify_state_change()

    def fail_task(self, task_id: str, error: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.status = ExecutionState.FAILED
            task.error_message = error
            task.completed_at = datetime.now().isoformat()
            self._save_persisted_state()
            self._notify_state_change()

    def cancel_task(self, task_id: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            if task.status in [ExecutionState.PENDING, ExecutionState.RUNNING]:
                task.status = ExecutionState.CANCELLED
                task.completed_at = datetime.now().isoformat()
                task.progress_message = "Cancelado"
            self._save_persisted_state()
            self._notify_state_change()

    def clear_completed_tasks(self):
        with self._lock:
            completed_ids = [
                task_id for task_id, task in self._tasks.items()
                if task.status in [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED]
            ]
            for task_id in completed_ids:
                del self._tasks[task_id]
                self._callbacks.pop(task_id, None)
            self._save_persisted_state()
            self._notify_state_change()

    def _save_persisted_state(self):
        """Persiste o estado em arquivo JSON"""
        try:
            state = {
                "tasks": [t.to_dict() for t in self._tasks.values()],
                "saved_at": datetime.now().isoformat()
            }
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.exception(f"Erro ao salvar estado persistido")

    def _load_persisted_state(self):
        """Carrega estado persistido do arquivo JSON"""
        try:
            if not self._state_file.exists():
                return

            with open(self._state_file, "r") as f:
                state = json.load(f)

            # Recuperar tarefas
            for task_data in state.get("tasks", []):
                task = ExecutionTask.from_dict(task_data)
                self._tasks[task.id] = task

                # Se estava em execução ou pendente, marcar como interrompida (não failed)
                if task.status in (ExecutionState.RUNNING, ExecutionState.PENDING):
                    task.status = "interrupted"
                    task.error_message = "Aplicação foi fechada durante a execução - tarefa interrompida"

            # Limpar tarefas muito antigas da memória (>7 dias)
            self.clear_old_tasks(days=7)
            logger.info(f"Carregadas {len(self._tasks)} tarefas persistidas")
        except Exception as e:
            logger.error(f"Erro ao carregar estado persistido: {e}")

    def export_tasks_for_web(self, user_id: str = None) -> List[Dict]:
        """Exporta tarefas em formato compatível com web para sincronização"""
        with self._lock:
            tasks = [
                t.to_dict() for t in self._tasks.values()
                if not user_id or t.user_id == user_id
            ]
            return tasks

    def clear_old_tasks(self, days: int = 7):
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        with self._lock:
            old_ids = []
            for task_id, task in self._tasks.items():
                if task.completed_at:
                    try:
                        completed_time = datetime.fromisoformat(task.completed_at).timestamp()
                        if completed_time < cutoff_time:
                            old_ids.append(task_id)
                    except Exception:
                        pass

            for task_id in old_ids:
                del self._tasks[task_id]
                self._callbacks.pop(task_id, None)

            if old_ids:
                self._save_persisted_state()
                self._notify_state_change()


_execution_manager = None
_execution_manager_lock = threading.Lock()


def get_execution_manager(storage: StorageManager = None) -> ExecutionManager:
    global _execution_manager
    with _execution_manager_lock:
        if _execution_manager is None:
            _execution_manager = ExecutionManager(storage)
        return _execution_manager
