"""
Concurrent Tasks Limiter - Controla execução simultânea de tarefas
"""
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Representa uma tarefa em execução"""
    task_id: str
    tool_name: str
    user_id: str
    start_time: datetime
    status: str = "running"  # running, completed, failed
    
    def is_active(self) -> bool:
        """Verifica se tarefa ainda está ativa"""
        return self.status == "running"


class ConcurrentTasksLimiter:
    """
    Gerencia limite de tarefas simultâneas por plano
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._active_tasks: Dict[str, List[Task]] = {}  # user_id -> [tasks]
    
    def register_task(self, user_id: str, task_id: str, tool_name: str) -> bool:
        """
        Registra uma nova tarefa
        
        Args:
            user_id: ID do usuário
            task_id: ID único da tarefa
            tool_name: Nome da ferramenta
            
        Returns:
            True se tarefa foi registrada, False se atingiu limite
        """
        with self._lock:
            if user_id not in self._active_tasks:
                self._active_tasks[user_id] = []
            
            # Contar apenas tarefas ativas
            active = [t for t in self._active_tasks[user_id] if t.is_active()]
            
            task = Task(
                task_id=task_id,
                tool_name=tool_name,
                user_id=user_id,
                start_time=datetime.now()
            )
            
            self._active_tasks[user_id].append(task)
            logger.info(f"Tarefa {task_id} registrada para {user_id}")
            return True
    
    def complete_task(self, user_id: str, task_id: str, status: str = "completed") -> bool:
        """
        Marca uma tarefa como concluída
        
        Args:
            user_id: ID do usuário
            task_id: ID da tarefa
            status: 'completed' ou 'failed'
            
        Returns:
            True se tarefa foi encontrada e atualizada
        """
        with self._lock:
            if user_id not in self._active_tasks:
                return False
            
            for task in self._active_tasks[user_id]:
                if task.task_id == task_id:
                    task.status = status
                    logger.info(f"Tarefa {task_id} finalizada com status: {status}")
                    return True
            
            return False
    
    def get_active_task_count(self, user_id: str) -> int:
        """Retorna número de tarefas ativas para um usuário"""
        with self._lock:
            if user_id not in self._active_tasks:
                return 0
            
            active = [t for t in self._active_tasks[user_id] if t.is_active()]
            return len(active)
    
    def get_active_tasks(self, user_id: str) -> List[Task]:
        """Retorna lista de tarefas ativas"""
        with self._lock:
            if user_id not in self._active_tasks:
                return []
            
            return [t for t in self._active_tasks[user_id] if t.is_active()]
    
    def clear_old_tasks(self, user_id: str, keep_last_n: int = 50) -> None:
        """
        Remove tarefas concluídas antigas (mantém apenas as últimas)
        
        Args:
            user_id: ID do usuário
            keep_last_n: Número de tarefas concluídas a manter
        """
        with self._lock:
            if user_id not in self._active_tasks:
                return
            
            # Separar ativas de concluídas
            active = [t for t in self._active_tasks[user_id] if t.is_active()]
            completed = [t for t in self._active_tasks[user_id] if not t.is_active()]
            
            # Manter últimas N concluídas (ordenadas por data)
            completed.sort(key=lambda t: t.start_time, reverse=True)
            completed_kept = completed[:keep_last_n]
            
            # Recombinar
            self._active_tasks[user_id] = active + completed_kept
            logger.debug(f"Limpeza de tarefas para {user_id}: {len(completed) - len(completed_kept)} removidas")
    
    def cancel_task(self, user_id: str, task_id: str) -> bool:
        """Cancela uma tarefa em execução"""
        return self.complete_task(user_id, task_id, "cancelled")


# Singleton global
_limiter_instance: Optional[ConcurrentTasksLimiter] = None


def get_task_limiter() -> ConcurrentTasksLimiter:
    """Obtém instância global do limitador"""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = ConcurrentTasksLimiter()
    return _limiter_instance
