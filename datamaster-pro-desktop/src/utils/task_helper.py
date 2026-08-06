"""
Task Helper - Helper para tool_pages integrarem com o TaskManager
"""
import json
import os
import threading
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.tasks.task_executor import task_executor
from src.core.storage.storage_manager import StorageManager


class TaskHelper:
    """Helper para gerenciar tarefas nas tool_pages"""
    
    def __init__(self, tool_name: str, storage: StorageManager = None):
        self.tool_name = tool_name
        self.storage = storage or StorageManager()
        self.task_id = None
        self._current_task = None
    
    def start_task(self, input_params: dict, on_progress=None, on_log=None) -> tuple[str, str]:
        """Inicia uma nova tarefa"""
        user_data = self.storage.get_saved_session()
        user_id = user_data.get("id") if user_data else "unknown"
        
        active_tasks = self.storage.get_active_tasks()
        for task in active_tasks:
            if task.get("tool_name") == self.tool_name:
                return None, f"Uma tarefa de {self.tool_name} já está em execução"
        
        active_count = self.storage.get_running_tasks_count()
        user_plan = user_data.get("plan", "gratis") if user_data else "gratis"
        plan_type = config.PlanType[user_plan.upper()] if user_plan.upper() in config.PlanType.__members__ else config.PlanType.GRATIS
        plan_limits = config.PLAN_LIMITS.get(plan_type, config.PLAN_LIMITS[config.PlanType.GRATIS])
        max_concurrent = plan_limits.get("max_concurrent_tasks", 1)
        
        if active_count >= max_concurrent:
            return None, f"Limite de {max_concurrent} tarefas simultâneas atingido"
        
        self.task_id = str(datetime.now().timestamp()).replace(".", "")
        
        task_data = {
            "id": self.task_id,
            "tool_name": self.tool_name,
            "status": "running",
            "progress_percent": 0,
            "progress_message": "Iniciando...",
            "input_params": json.dumps(input_params),
            "output_path": "",
            "log_text": "",
            "rows_processed": 0,
            "hours_saved": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "user_id": user_id,
            "error_message": ""
        }
        
        self.storage.save_task(task_data)
        self._current_task = task_data
        
        return self.task_id, None
    
    def update_progress(self, current: int, total: int, percentage: int):
        """Atualiza o progresso da tarefa"""
        if not self.task_id:
            return
        
        message = f"Processando {current}/{total} ({percentage}%)"
        self.storage.update_task(self.task_id, {
            "progress_percent": percentage,
            "progress_message": message
        })
    
    def add_log(self, message: str):
        """Adiciona uma mensagem ao log"""
        if not self.task_id:
            return
        
        task = self.storage.get_task(self.task_id)
        if task:
            current_log = task.get("log_text", "")
            new_log = current_log + message + "\n"
            self.storage.update_task(self.task_id, {"log_text": new_log[-5000:]})
    
    def complete(self, output_path: str = "", rows: int = 0, hours: float = 0):
        """Marca a tarefa como concluída"""
        if not self.task_id:
            return
        
        self.storage.update_task(self.task_id, {
            "status": "completed",
            "progress_percent": 100,
            "progress_message": "Concluído",
            "output_path": output_path,
            "rows_processed": rows,
            "hours_saved": hours,
            "completed_at": datetime.now().isoformat()
        })
        
        self._send_notification()
    
    def fail(self, error: str):
        """Marca a tarefa como falhou"""
        if not self.task_id:
            return
        
        self.storage.update_task(self.task_id, {
            "status": "failed",
            "progress_message": f"Erro: {error}",
            "error_message": error,
            "completed_at": datetime.now().isoformat()
        })
    
    def cancel(self):
        """Cancela a tarefa"""
        if not self.task_id:
            return
        
        task = self.storage.get_task(self.task_id)
        if task and task.get("status") in ["pending", "running"]:
            self.storage.update_task(self.task_id, {
                "status": "cancelled",
                "completed_at": datetime.now().isoformat()
            })
    
    def _send_notification(self):
        """Envia notificação desktop"""
        try:
            from src.utils.notifications import notification_manager
            notification_manager.task_completed_async(
                tool_name=self.tool_name,
            )
        except Exception:
            pass


def start_tool_task(tool_name: str, input_params: dict, storage: StorageManager = None) -> tuple[TaskHelper, str]:
    """
    Função convenience para iniciar uma tarefa de ferramenta
    Retorna (TaskHelper, error_message)
    """
    helper = TaskHelper(tool_name, storage)
    task_id, error = helper.start_task(input_params)
    if error:
        return None, error
    return helper, None