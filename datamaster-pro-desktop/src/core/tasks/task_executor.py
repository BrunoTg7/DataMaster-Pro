"""
TaskExecutor - Motor unificado de execução de tarefas
Unifica task_manager + global_executor + execution_manager em um único sistema.
Suporta:
- Execução paralela com até 2 tarefas simultâneas (PRO)
- Ferramentas registradas via register_tool() e execução automática
- Submissão de funções arbitrárias via submit() com callbacks
- Persistência via StorageManager (SQLite)
- Notificações desktop
- Recuperação de tarefas interrompidas
"""
import uuid
import threading
import json
import logging
import inspect
from datetime import datetime
from typing import Optional, Dict, List, Callable, Any
from pathlib import Path
import os
import sys

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.storage.storage_manager import StorageManager


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class TaskInfo:
    """Dados internos de uma tarefa em memória"""
    def __init__(self, task_id: str, tool_name: str, tool_display_name: str, user_id: str = None):
        self.id = task_id
        self.tool_name = tool_name
        self.tool_display_name = tool_display_name
        self.user_id = user_id or ""
        self.status = TaskStatus.PENDING
        self.progress_percent = 0
        self.progress_message = "Aguardando..."
        self.error_message = ""
        self.rows_processed = 0
        self.hours_saved = 0
        self.output_path = ""
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.completed_at: Optional[str] = None
        self.log_messages: List[str] = []
        self.input_params = "{}"
        self.result_data: Dict = {}
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None


class TaskExecutor:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage: StorageManager = None):
        if self._initialized:
            return
        self._storage = storage or StorageManager()
        self._tasks: Dict[str, TaskInfo] = {}
        self._task_lock = threading.RLock()
        self._tool_registry: Dict[str, type] = {}
        self._callbacks: Dict[str, Dict[str, Callable]] = {}
        self._new_task_callbacks: List[Callable] = []
        self._state_change_callbacks: List[Callable] = []
        self._initialized = True

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, value):
        self._storage = value

    @property
    def max_concurrent(self) -> int:
        session = self._storage.get_saved_session()
        return 2 if session and session.get("plan") == "pro" else 1

    # ── Tool registry ──────────────────────────────────────────────────────

    def register_tool(self, tool_name: str, tool_class: type):
        self._tool_registry[tool_name] = tool_class

    # ── Callbacks ───────────────────────────────────────────────────────────

    def on_new_task(self, callback: Callable):
        self._new_task_callbacks.append(callback)

    def register_state_change_callback(self, callback: Callable):
        self._state_change_callbacks.append(callback)

    def _notify_new_task(self):
        for cb in self._new_task_callbacks:
            try:
                cb()
            except Exception:
                pass

    def _notify_state_change(self):
        with self._task_lock:
            active = self.get_active_tasks()
        for cb in self._state_change_callbacks:
            try:
                cb(active)
            except Exception:
                pass

    # ── Submit (função arbitrária em thread) ────────────────────────────────

    def submit(
        self,
        tool_name: str,
        tool_display_name: str,
        execute_func: Callable[[], dict],
        on_complete: Callable[[dict], None] = None,
        user_id: str = None,
    ) -> tuple[Optional[str], Optional[str]]:
        with self._task_lock:
            running = [t for t in self._tasks.values()
                       if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)]
            if len(running) >= self.max_concurrent:
                return None, f"Limite de {self.max_concurrent} tarefa(s) simultânea(s) atingido"

            same_tool = [t for t in running if t.tool_name == tool_name]
            if same_tool:
                return None, f"Uma tarefa de {tool_display_name} já está em execução"

            task_id = str(uuid.uuid4())
            task = TaskInfo(task_id, tool_name, tool_display_name, user_id)
            self._tasks[task_id] = task
            self._save_to_storage(task)

        self._notify_new_task()

        def run():
            try:
                with self._task_lock:
                    task.status = TaskStatus.RUNNING
                    task.progress_message = "Executando..."
                    self._save_to_storage(task)
                self._notify_state_change()
                logger.info("%s iniciada (id=%s)", tool_display_name, task_id[:8])

                result = execute_func()

                if self.is_cancelled(task_id):
                    return

                with self._task_lock:
                    task.status = TaskStatus.COMPLETED
                    task.progress_percent = 100
                    task.progress_message = "Concluído"
                    task.completed_at = datetime.now().isoformat()
                    task.updated_at = task.completed_at
                    if isinstance(result, dict):
                        task.rows_processed = result.get("rows_processed") or result.get("collected") or result.get("total_rows", 0)
                        task.output_path = result.get("output_path") or result.get("output_file", "")
                        task.hours_saved = result.get("hours_saved", 0)
                    self._save_to_storage(task)
                self._notify_state_change()
                logger.info("%s concluída (%d linhas)", tool_display_name, task.rows_processed)

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
                    task.updated_at = task.completed_at
                    self._save_to_storage(task)
                self._notify_state_change()
                logger.error("%s falhou: %s", tool_display_name, e)
                if on_complete:
                    on_complete({"success": False, "error": str(e)})

        task._thread = threading.Thread(target=run, daemon=True)
        task._thread.start()

        return task_id, None

    # ── Create task via tool registry ───────────────────────────────────────

    def create_task(
        self,
        tool_name: str,
        input_params: dict,
        progress_callback: Callable = None,
        log_callback: Callable = None,
        auto_execute: bool = False,
        tool_display_name: str = None,
    ) -> tuple[Optional[str], Optional[str]]:
        user_data = self._storage.get_saved_session()
        user_id = user_data.get("id") if user_data else "unknown"

        with self._task_lock:
            same_tool_running = [t for t in self._tasks.values()
                                 if t.tool_name == tool_name
                                 and t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)]
            if same_tool_running:
                return None, f"Uma tarefa de {tool_display_name or tool_name} já está em execução"

            active_count = len([t for t in self._tasks.values()
                                if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)])
            if active_count >= self.max_concurrent:
                return None, f"Limite de {self.max_concurrent} tarefas simultâneas atingido. Execute ferramentas diferentes."

            task_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()

            task = TaskInfo(task_id, tool_name, tool_display_name or tool_name, user_id)
            task.input_params = json.dumps(input_params)
            task.created_at = created_at
            task.updated_at = created_at
            self._tasks[task_id] = task
            self._save_to_storage(task)

            self._callbacks[task_id] = {
                "progress": progress_callback,
                "log": log_callback,
            }

        self._notify_new_task()

        if auto_execute:
            thread = threading.Thread(target=self._execute_task, args=(task_id,), daemon=True)
            thread.start()

        return task_id, None

    def _execute_task(self, task_id: str):
        task = self._tasks.get(task_id)
        if not task:
            return

        with self._task_lock:
            task.status = TaskStatus.RUNNING
            self._save_to_storage(task)

        tool_name = task.tool_name
        input_params = json.loads(task.input_params)
        tool_class = self._tool_registry.get(tool_name)
        if not tool_class:
            self.fail_task(task_id, f"Ferramenta {tool_name} não registrada")
            return

        output_dir = Path(config.OUTPUT_DIR) / tool_name / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        with self._task_lock:
            callbacks = dict(self._callbacks.get(task_id, {}))

        accumulated_log = []

        def progress_handler(current, total, percentage):
            self.update_progress(task_id, percentage, f"Processando {current}/{total}")
            if callbacks.get("progress"):
                try:
                    callbacks["progress"](current, total, percentage)
                except Exception:
                    pass

        def log_handler(message):
            accumulated_log.append(message)
            if callbacks.get("log"):
                try:
                    callbacks["log"](message)
                except Exception:
                    pass
            task.log_messages = accumulated_log[-100:]

        try:
            sig = inspect.signature(tool_class.__init__)
            init_kwargs = {}
            if 'progress_callback' in sig.parameters:
                init_kwargs['progress_callback'] = progress_handler
            if 'log_callback' in sig.parameters:
                init_kwargs['log_callback'] = log_handler
            tool_instance = tool_class(**init_kwargs)

            execute_method = getattr(tool_instance, "execute", None) or getattr(tool_instance, "run", None)
            if not execute_method:
                raise AttributeError(f"{tool_name} não tem método execute() ou run()")

            result = execute_method(input_params)

            output_path = ""
            rows_processed = 0
            hours_saved = 0

            if isinstance(result, dict):
                output_path = result.get("output_path", str(output_dir))
                rows_processed = result.get("rows_processed", 0)
                hours_saved = result.get("hours_saved", 0)

            self.complete_task(task_id, output_path, rows_processed, hours_saved)

        except Exception as e:
            self.fail_task(task_id, str(e))

        finally:
            with self._task_lock:
                self._callbacks.pop(task_id, None)

    # ── Progress & lifecycle ────────────────────────────────────────────────

    def update_progress(self, task_id: str, percent: int, message: str = ""):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task or task._cancel_event.is_set():
                return
            task.status = TaskStatus.RUNNING
            task.progress_percent = min(100, max(0, percent))
            if message:
                task.progress_message = message
            task.updated_at = datetime.now().isoformat()
            self._save_to_storage(task)

    def add_log(self, task_id: str, message: str):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            ts = datetime.now().strftime("%H:%M:%S")
            task.log_messages.append(f"[{ts}] {message}")
            task.log_messages = task.log_messages[-100:]

    def complete_task(self, task_id: str, output_path: str = "", rows: int = 0, hours: float = 0):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.status = TaskStatus.COMPLETED
            task.progress_percent = 100
            task.progress_message = "Concluído"
            task.output_path = output_path
            task.rows_processed = rows
            task.hours_saved = hours
            task.completed_at = datetime.now().isoformat()
            task.updated_at = task.completed_at
            self._save_to_storage(task)
        self._notify_state_change()
        self._send_notification(task_id)

    def fail_task(self, task_id: str, error: str):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.status = TaskStatus.FAILED
            task.error_message = error
            task.progress_message = f"Erro: {error}"
            task.completed_at = datetime.now().isoformat()
            task.updated_at = task.completed_at
            self._save_to_storage(task)
        self._notify_state_change()

    def cancel_task(self, task_id: str) -> bool:
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task or task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
                return False
            task._cancel_event.set()
            task.status = TaskStatus.CANCELLED
            task.progress_message = "Cancelado"
            task.completed_at = datetime.now().isoformat()
            task.updated_at = task.completed_at
            self._save_to_storage(task)
        self._notify_state_change()
        return True

    def is_cancelled(self, task_id: str) -> bool:
        with self._task_lock:
            task = self._tasks.get(task_id)
            return task._cancel_event.is_set() if task else True

    # ── Query ───────────────────────────────────────────────────────────────

    def get_tasks(self, status_filter: str = None) -> List[dict]:
        with self._task_lock:
            if status_filter:
                result = [self._task_to_dict(t) for t in self._tasks.values()
                          if t.status == status_filter]
            else:
                result = [self._task_to_dict(t) for t in self._tasks.values()]
            # Se houver poucas ou nenhuma tarefa em memória, buscar do banco
            if len(result) < 50:
                db_tasks = self._storage.get_all_tasks(
                    status_filter=status_filter, limit=100
                ) or []
                mem_ids = {t["id"] for t in result}
                for db_task in db_tasks:
                    if db_task["id"] not in mem_ids:
                        result.append(db_task)
                        mem_ids.add(db_task["id"])
            return result[:200]

    def get_task(self, task_id: str) -> Optional[dict]:
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task:
                return self._task_to_dict(task)
            db_task = self._storage.get_task(task_id)
            return db_task if db_task else None

    def get_active_tasks(self) -> List[dict]:
        with self._task_lock:
            return [self._task_to_dict(t) for t in self._tasks.values()
                    if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)]

    def get_running_count(self) -> int:
        with self._task_lock:
            return len([t for t in self._tasks.values()
                        if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)])

    # ── Recovery ────────────────────────────────────────────────────────────

    def recover_interrupted_tasks(self):
        with self._task_lock:
            stale = self._storage.get_all_tasks(status_filter=None) or []
            for row in stale:
                if row.get("status") in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.INTERRUPTED):
                    input_params = row.get("input_params", "{}")
                    if not input_params or input_params == "{}":
                        self._storage.delete_task(row["id"])
                        continue
                    if row["id"] in self._tasks:
                        continue
                    task = TaskInfo(
                        task_id=row["id"],
                        tool_name=row.get("tool_name", ""),
                        tool_display_name=row.get("tool_display_name", row.get("tool_name", "")),
                        user_id=row.get("user_id"),
                    )
                    task.status = TaskStatus.INTERRUPTED
                    task.progress_percent = row.get("progress_percent", 0)
                    task.progress_message = "Interrompido - app foi fechado"
                    task.input_params = input_params
                    task.created_at = row.get("created_at", task.created_at)
                    task.completed_at = datetime.now().isoformat()
                    task.updated_at = task.completed_at
                    task.rows_processed = row.get("rows_processed", 0)
                    task.error_message = row.get("error_message", "")
                    self._tasks[task.id] = task
                    self._save_to_storage(task)

            for task in self._tasks.values():
                if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                    task.status = TaskStatus.INTERRUPTED
                    task.progress_message = "Interrompido - aplicação foi fechada"
                    task.completed_at = datetime.now().isoformat()
                    task.updated_at = task.completed_at
                    self._save_to_storage(task)

    # ── Restart / Requeue ───────────────────────────────────────────────────

    def restart_task(self, task_id: str) -> tuple[Optional[str], Optional[str]]:
        task = self._tasks.get(task_id)
        if not task:
            db_task = self._storage.get_task(task_id)
            if not db_task:
                return None, "Tarefa não encontrada"
            if db_task.get("status") != TaskStatus.INTERRUPTED:
                return None, "Tarefa não pode ser reiniciada"
            input_params = json.loads(db_task.get("input_params", "{}")) if db_task.get("input_params") else {}
            tool_name = db_task.get("tool_name", "")
            display_name = db_task.get("tool_display_name", tool_name)
            return self.create_task(
                tool_name, input_params,
                auto_execute=True,
                tool_display_name=display_name,
            )
        if task.status != TaskStatus.INTERRUPTED:
            return None, "Tarefa não pode ser reiniciada"

        input_params = json.loads(task.input_params) if task.input_params else {}
        return self.create_task(
            task.tool_name, input_params,
            auto_execute=True,
            tool_display_name=task.tool_display_name,
        )

    def requeue_task(self, task_id: str) -> tuple[Optional[str], Optional[str]]:
        task = self._tasks.get(task_id)
        if not task:
            return None, "Tarefa não encontrada"
        if task.status not in (TaskStatus.INTERRUPTED, TaskStatus.CANCELLED, TaskStatus.FAILED):
            return None, "Tarefa não pode ser reenviada"

        with self._task_lock:
            task.status = TaskStatus.PENDING
            task.progress_percent = 0
            task.progress_message = "Reenviado - acesse a ferramenta para executar"
            task.error_message = ""
            task.updated_at = datetime.now().isoformat()
            self._save_to_storage(task)

        return task_id, None

    # ── Maintenance ─────────────────────────────────────────────────────────

    def clear_old_tasks(self, days: int = 7):
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        with self._task_lock:
            old_ids = [
                tid for tid, t in self._tasks.items()
                if t.completed_at and
                datetime.fromisoformat(t.completed_at).timestamp() < cutoff
            ]
            for tid in old_ids:
                del self._tasks[tid]
                self._callbacks.pop(tid, None)

    def clear_completed_tasks(self):
        with self._task_lock:
            done_ids = [
                tid for tid, t in self._tasks.items()
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            ]
            for tid in done_ids:
                del self._tasks[tid]
                self._callbacks.pop(tid, None)

    # ── Export ──────────────────────────────────────────────────────────────

    def export_tasks_for_web(self, user_id: str = None) -> List[Dict]:
        with self._task_lock:
            return [
                self._task_to_dict(t) for t in self._tasks.values()
                if not user_id or t.user_id == user_id
            ]

    # ── Internal ────────────────────────────────────────────────────────────

    def _task_to_dict(self, task: TaskInfo) -> dict:
        return {
            "id": task.id,
            "tool_name": task.tool_name,
            "tool_display_name": task.tool_display_name,
            "status": task.status,
            "progress_percent": task.progress_percent,
            "progress_message": task.progress_message,
            "error_message": task.error_message,
            "rows_processed": task.rows_processed,
            "hours_saved": task.hours_saved,
            "output_path": task.output_path,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at or "",
            "user_id": task.user_id,
            "input_params": task.input_params,
            "log_text": "\n".join(task.log_messages[-20:]),
            "log_messages": task.log_messages[-50:],
            "result_data": task.result_data,
        }

    def _save_to_storage(self, task: TaskInfo):
        try:
            d = self._task_to_dict(task)
            existing = self._storage.get_task(task.id)
            if existing:
                self._storage.update_task(task.id, d)
            else:
                self._storage.save_task(d)
        except Exception as e:
            logger.error(f"Erro ao persistir tarefa {task.id}: {e}")

    def _send_notification(self, task_id: str):
        try:
            from src.utils.notifications import notification_manager
            task = self._tasks.get(task_id)
            if task:
                notification_manager.task_completed_async(
                    tool_name=task.tool_display_name,
                    records_count=task.rows_processed,
                    hours_saved=task.hours_saved,
                )
        except Exception:
            pass


# Singleton
task_manager = TaskExecutor()

# Alias unificado para consumo externo
task_executor = task_manager
