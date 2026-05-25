"""
Task Scheduler - Agendamento de tarefas com suporte a Cron
Suporta execução quando app aberto (PRO) e background (ENTERPRISE)
"""
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from enum import Enum
import subprocess
import os

logger = logging.getLogger(__name__)


class ScheduleFrequency(str, Enum):
    """Frequências de agendamento suportadas"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM_CRON = "custom_cron"


@dataclass
class ScheduledTask:
    """Representa uma tarefa agendada"""
    task_id: str
    user_id: str
    tool_name: str
    tool_action: str  # ex: 'consolidate', 'categorize'
    input_files: List[str]  # Paths dos arquivos de entrada
    schedule_frequency: str  # 'daily', 'weekly', 'monthly', 'custom_cron'
    cron_expression: Optional[str] = None  # Para custom_cron
    time_of_day: Optional[str] = None  # Para daily/weekly/monthly (HH:MM)
    day_of_week: Optional[int] = None  # 0=Mon, 6=Sun (para weekly)
    day_of_month: Optional[int] = None  # 1-31 (para monthly)
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    created_at: str = None
    config: Optional[Dict] = None  # Config específica da ferramenta
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "tool_name": self.tool_name,
            "tool_action": self.tool_action,
            "input_files": self.input_files,
            "schedule_frequency": self.schedule_frequency,
            "cron_expression": self.cron_expression,
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "day_of_month": self.day_of_month,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "created_at": self.created_at,
            "config": self.config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Cria a partir de dicionário"""
        return cls(**data)
    
    def should_run_now(self) -> bool:
        """Verifica se tarefa deve ser executada agora"""
        if not self.enabled:
            return False
        
        now = datetime.now()
        next_run = datetime.fromisoformat(self.next_run) if self.next_run else now
        
        return now >= next_run
    
    def calculate_next_run(self) -> datetime:
        """Calcula próximo tempo de execução"""
        now = datetime.now()
        
        if self.schedule_frequency == ScheduleFrequency.DAILY:
            hour, minute = map(int, self.time_of_day.split(":"))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif self.schedule_frequency == ScheduleFrequency.WEEKLY:
            hour, minute = map(int, self.time_of_day.split(":"))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = (self.day_of_week - next_run.weekday()) % 7
            if days_ahead == 0 and next_run <= now:
                days_ahead = 7
            next_run += timedelta(days=days_ahead)
            return next_run
        
        elif self.schedule_frequency == ScheduleFrequency.MONTHLY:
            hour, minute = map(int, self.time_of_day.split(":"))
            try:
                next_run = now.replace(
                    day=self.day_of_month,
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0
                )
                if next_run <= now:
                    if next_run.month == 12:
                        next_run = next_run.replace(year=next_run.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=next_run.month + 1)
            except ValueError:
                # Dia inválido para este mês
                next_run = now + timedelta(days=1)
            return next_run
        
        elif self.schedule_frequency == ScheduleFrequency.CUSTOM_CRON:
            # Para cron custom, usar biblioteca croniter
            try:
                from croniter import croniter
                cron = croniter(self.cron_expression, now)
                return datetime.fromtimestamp(cron.get_next(float))
            except ImportError:
                logger.warning("croniter não instalado, usando daily fallback")
                return now + timedelta(days=1)
        
        return now + timedelta(days=1)


class TaskScheduler:
    """
    Gerencia agendamento de tarefas
    Suporta: app aberto (PRO) e background via Windows Task Scheduler (ENTERPRISE)
    """
    
    def __init__(self, storage_manager=None):
        self._storage = storage_manager
        self._running_tasks: Dict[str, ScheduledTask] = {}
        self._task_callbacks: Dict[str, Callable] = {}
    
    def create_task(self,
                   user_id: str,
                   tool_name: str,
                   tool_action: str,
                   input_files: List[str],
                   frequency: str,
                   time_of_day: Optional[str] = None,
                   cron_expression: Optional[str] = None,
                   **kwargs) -> ScheduledTask:
        """
        Cria uma tarefa agendada
        """
        import uuid
        
        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            user_id=user_id,
            tool_name=tool_name,
            tool_action=tool_action,
            input_files=input_files,
            schedule_frequency=frequency,
            time_of_day=time_of_day,
            cron_expression=cron_expression,
            created_at=datetime.now().isoformat(),
            **kwargs
        )
        
        task.next_run = task.calculate_next_run().isoformat()
        
        # Salvar no storage
        if self._storage:
            try:
                self._storage.save_scheduled_task(task)
                logger.info(f"Tarefa agendada criada: {task.task_id}")
            except Exception as e:
                logger.error(f"Erro ao salvar tarefa: {e}")
        
        return task
    
    def get_tasks_for_user(self, user_id: str) -> List[ScheduledTask]:
        """Recupera todas as tarefas de um usuário"""
        if not self._storage:
            return []
        
        try:
            return self._storage.get_scheduled_tasks(user_id)
        except Exception as e:
            logger.error(f"Erro ao recuperar tarefas: {e}")
            return []
    
    def get_due_tasks(self, user_id: str) -> List[ScheduledTask]:
        """Retorna tarefas que devem ser executadas agora"""
        tasks = self.get_tasks_for_user(user_id)
        return [t for t in tasks if t.should_run_now()]
    
    def register_task_callback(self, tool_name: str, callback: Callable):
        """
        Registra callback para executar tarefa
        
        Args:
            tool_name: Nome da ferramenta
            callback: Função que executa a ferramenta (receberá task como argumento)
        """
        self._task_callbacks[tool_name] = callback
    
    def execute_task(self, task: ScheduledTask) -> bool:
        """
        Executa uma tarefa agendada
        
        Returns:
            True se executada com sucesso
        """
        if task.tool_name not in self._task_callbacks:
            logger.error(f"Sem callback para ferramenta: {task.tool_name}")
            return False
        
        try:
            callback = self._task_callbacks[task.tool_name]
            callback(task)
            
            # Atualizar last_run e next_run
            task.last_run = datetime.now().isoformat()
            task.next_run = task.calculate_next_run().isoformat()
            
            if self._storage:
                self._storage.update_scheduled_task(task)
            
            logger.info(f"Tarefa executada: {task.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao executar tarefa {task.task_id}: {e}")
            return False
    
    def disable_task(self, task_id: str) -> bool:
        """Desabilita uma tarefa"""
        if self._storage:
            try:
                self._storage.disable_scheduled_task(task_id)
                return True
            except Exception as e:
                logger.error(f"Erro ao desabilitar tarefa: {e}")
        return False
    
    def delete_task(self, task_id: str) -> bool:
        """Deleta uma tarefa"""
        if self._storage:
            try:
                self._storage.delete_scheduled_task(task_id)
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar tarefa: {e}")
        return False
    
    def create_windows_scheduled_task(self, task: ScheduledTask, app_path: str) -> bool:
        """
        Cria tarefa no Windows Task Scheduler (Enterprise only)
        
        Args:
            task: ScheduledTask
            app_path: Caminho do executável da aplicação
            
        Returns:
            True se criada com sucesso
        """
        try:
            import sys
            
            if sys.platform != "win32":
                logger.warning("Windows Task Scheduler disponível apenas no Windows")
                return False
            
            # Construir comando PowerShell para registrar tarefa
            task_name = f"DataMaster_{task.task_id}"
            
            # Script Python para executar tarefa
            runner_script = f"""
import sys
sys.path.insert(0, '{os.path.dirname(app_path)}')
from src.core.roi_logger import get_roi_manager
from src.core.task_scheduler import get_task_scheduler

scheduler = get_task_scheduler()
task = scheduler.get_task('{task.task_id}')
if task:
    scheduler.execute_task(task)
            """
            
            # Criar arquivo de script temporário
            script_path = os.path.join(os.environ.get('TEMP', '/tmp'), f"task_{task.task_id}.py")
            with open(script_path, 'w') as f:
                f.write(runner_script)
            
            # Comando PowerShell para registrar tarefa
            ps_command = f"""
$trigger = New-ScheduledTaskTrigger -AtStartup
$action = New-ScheduledTaskAction -Execute 'python' -Argument '"{script_path}"'
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "{task_name}" -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Force
            """
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Tarefa Windows criada: {task_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar tarefa Windows: {e}")
            return False


# Singleton
_scheduler_instance: Optional[TaskScheduler] = None


def get_task_scheduler(storage_manager=None) -> TaskScheduler:
    """Factory para obter instância do Task Scheduler"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler(storage_manager)
    
    return _scheduler_instance
