"""
Task Manager - Gerenciador de tarefas em segundo plano
Permite 2 tarefas simultâneas de ferramentas diferentes
"""
import uuid
import threading
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Callable
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.storage.storage_manager import StorageManager


class TaskManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, storage: StorageManager = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, storage: StorageManager = None):
        if self._initialized:
            return
        self.storage = storage or StorageManager()
        self._running_tasks: Dict[str, threading.Thread] = {}
        self._callbacks: Dict[str, dict] = {}
        self._task_lock = threading.Lock()
        self._tool_registry: Dict[str, type] = {}
        self._initialized = True

    def register_tool(self, tool_name: str, tool_class: type):
        """Registra uma ferramenta para uso nas tarefas"""
        self._tool_registry[tool_name] = tool_class

    @property
    def max_concurrent(self) -> int:
        """Retorna o limite de tarefas simultâneas baseado no plano"""
        session = self.storage.get_saved_session()
        return 2 if session and session.get("plan") == "pro" else 1

    def _is_tool_running(self, tool_name: str) -> bool:
        """Verifica se já tem tarefa da mesma ferramenta rodando"""
        active_tasks = self.storage.get_active_tasks()
        for task in active_tasks:
            if task.get("tool_name") == tool_name:
                return True
        return False

    def create_task(self, tool_name: str, input_params: dict, progress_callback: Callable = None, 
                    log_callback: Callable = None, auto_execute: bool = False, tool_display_name: str = None) -> tuple[Optional[str], Optional[str]]:
        """Cria uma nova tarefa
        
        Permite executar até 2 ferramentas DIFERENTES em paralelo.
        Não permite executar a mesma ferramenta duas vezes simultaneamente.
        """
        user_data = self.storage.get_saved_session()
        user_id = user_data.get("id") if user_data else "unknown"

        with self._task_lock:
            if self._is_tool_running(tool_name):
                return None, f"Uma tarefa de {tool_display_name or tool_name} já está em execução"

            active_count = self.storage.get_running_tasks_count()
            if active_count >= self.max_concurrent:
                return None, f"Limite de {self.max_concurrent} tarefas simultâneas atingido. Execute ferramentas diferentes."

            task_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()

            task_data = {
                "id": task_id,
                "tool_name": tool_name,
                "tool_display_name": tool_display_name or tool_name,
                "status": "pending",
                "progress_percent": 0,
                "progress_message": "Aguardando...",
                "input_params": json.dumps(input_params),
                "output_path": "",
                "log_text": "",
                "rows_processed": 0,
                "hours_saved": 0,
                "created_at": created_at,
                "updated_at": created_at,
                "user_id": user_id,
                "error_message": ""
            }

            self.storage.save_task(task_data)

            self._callbacks[task_id] = {
                "progress": progress_callback,
                "log": log_callback
            }

        if auto_execute:
            thread = threading.Thread(
                target=self._execute_task,
                args=(task_id,),
                daemon=True
            )
            thread.start()

        return task_id, None

    def _execute_task(self, task_id: str):
        """Executa a tarefa em background"""
        task = self.storage.get_task(task_id)
        if not task:
            return

        self.storage.update_task(task_id, {"status": "running"})

        tool_name = task.get("tool_name")
        input_params = json.loads(task.get("input_params", "{}"))
        user_id = task.get("user_id")

        tool_class = self._tool_registry.get(tool_name)
        if not tool_class:
            self.fail_task(task_id, f"Ferramenta {tool_name} não registrada")
            return

        output_dir = Path(config.OUTPUT_DIR) / tool_name / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        with self._task_lock:
            callbacks = self._callbacks.get(task_id, {})
        
        accumulated_log = []

        def progress_handler(current: int, total: int, percentage: int):
            self.update_progress(task_id, percentage, f"Processando {current}/{total}")
            if callbacks.get("progress"):
                try:
                    callbacks["progress"](current, total, percentage)
                except Exception:
                    pass

        def log_handler(message: str):
            accumulated_log.append(message)
            if callbacks.get("log"):
                try:
                    callbacks["log"](message)
                except Exception:
                    pass
            self.storage.update_task(task_id, {"log_text": "\n".join(accumulated_log[-100:])})

        try:
            tool_instance = tool_class(
                progress_callback=progress_handler,
                log_callback=log_handler
            )

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
                self._running_tasks.pop(task_id, None)

    def update_progress(self, task_id: str, percent: int, message: str):
        """Atualiza o progresso da tarefa"""
        self.storage.update_task(task_id, {
            "progress_percent": percent,
            "progress_message": message
        })

    def complete_task(self, task_id: str, output_path: str, rows: int, hours: float):
        """Marca a tarefa como concluída"""
        self.storage.update_task(task_id, {
            "status": "completed",
            "progress_percent": 100,
            "progress_message": "Concluído",
            "output_path": output_path,
            "rows_processed": rows,
            "hours_saved": hours,
            "completed_at": datetime.now().isoformat()
        })
        self._send_notification(task_id)

    def fail_task(self, task_id: str, error: str):
        """Marca a tarefa como falhou"""
        self.storage.update_task(task_id, {
            "status": "failed",
            "progress_message": f"Erro: {error}",
            "error_message": error,
            "completed_at": datetime.now().isoformat()
        })

    def cancel_task(self, task_id: str):
        """Cancela uma tarefa"""
        task = self.storage.get_task(task_id)
        if task and task.get("status") in ["pending", "running"]:
            self.storage.update_task(task_id, {
                "status": "cancelled",
                "completed_at": datetime.now().isoformat()
            })

    def restart_task(self, task_id: str) -> tuple[Optional[str], Optional[str]]:
        """Reinicia uma tarefa interrompida"""
        task = self.storage.get_task(task_id)
        if not task:
            return None, "Tarefa não encontrada"

        if task.get("status") != "interrupted":
            return None, "Tarefa não pode ser reiniciada"

        input_params = json.loads(task.get("input_params", "{}"))
        tool_name = task.get("tool_name")

        new_id, error = self.create_task(tool_name, input_params, auto_execute=True)
        return new_id, error

    def requeue_task(self, task_id: str) -> tuple[Optional[str], Optional[str]]:
        """Re-coloca uma tarefa interrompida como pendente
        (não executa automaticamente - usuário precisa ir na página da ferramenta)"""
        task = self.storage.get_task(task_id)
        if not task:
            return None, "Tarefa não encontrada"

        if task.get("status") not in ("interrupted", "cancelled", "failed"):
            return None, "Tarefa não pode ser reenviada"

        self.storage.update_task(task_id, {
            "status": "pending",
            "progress_percent": 0,
            "progress_message": "Reenviado - acesse a ferramenta para executar",
            "error_message": ""
        })
        return task_id, None

    def get_tasks(self, status_filter: str = None) -> List[dict]:
        """Retorna todas as tarefas"""
        return self.storage.get_all_tasks(status_filter)

    def get_task(self, task_id: str) -> Optional[dict]:
        """Retorna uma tarefa específica"""
        return self.storage.get_task(task_id)

    def get_active_tasks(self) -> List[dict]:
        """Retorna tarefas ativas (pending + running)"""
        return self.storage.get_active_tasks()

    def recover_interrupted_tasks(self):
        """Marca tarefas interrompidas ao iniciar app"""
        for status in ("running", "pending"):
            tasks = self.storage.get_all_tasks(status)
            for task in tasks:
                self.storage.update_task(task["id"], {
                    "status": "interrupted",
                    "progress_message": "Interrompido - clique para continuar"
                })

    def _send_notification(self, task_id: str):
        """Envia notificação desktop"""
        try:
            from src.utils.notifications import notification_manager
            task = self.storage.get_task(task_id)
            if task:
                notification_manager.send_async(
                    title=f"✅ {task['tool_name'].capitalize()} Concluído!",
                    message=f"Processadas {task.get('rows_processed', 0)} linhas"
                )
        except Exception:
            pass


task_manager = TaskManager()