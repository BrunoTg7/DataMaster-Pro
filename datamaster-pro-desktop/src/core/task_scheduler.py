"""
Task Scheduler - Agendamento de tarefas com suporte a Cron
Usa o TaskExecutor unificado para executar as tarefas agendadas.
Suporta execução quando app aberto (PRO) e background (ENTERPRISE)
"""
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from enum import Enum
import threading
import time

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
    tool_action: str
    input_files: List[str]
    schedule_frequency: str
    cron_expression: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    created_at: str = None
    config: Optional[Dict] = None
    task_name: Optional[str] = None
    execution_count: int = 0
    last_status: Optional[str] = None
    last_error: Optional[str] = None

    def to_dict(self) -> Dict:
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
            "task_name": self.task_name,
            "execution_count": self.execution_count,
            "last_status": self.last_status,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def should_run_now(self) -> bool:
        if not self.enabled:
            return False
        now = datetime.now()
        next_run = datetime.fromisoformat(self.next_run) if self.next_run else now
        return now >= next_run

    def calculate_next_run(self) -> datetime:
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
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                if next_run <= now:
                    if next_run.month == 12:
                        next_run = next_run.replace(year=next_run.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=next_run.month + 1)
            except ValueError:
                next_run = now + timedelta(days=1)
            return next_run

        elif self.schedule_frequency == ScheduleFrequency.CUSTOM_CRON:
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
    Gerencia agendamento de tarefas.
    Usa o TaskExecutor unificado para executar as tarefas.
    """

    def __init__(self, storage_manager=None, executor=None):
        from src.core.tasks.task_executor import task_executor as _default_executor

        self._storage = storage_manager
        self._executor = executor or _default_executor
        self._task_callbacks: Dict[str, Callable] = {}
        self._polling_thread: Optional[threading.Thread] = None
        self._polling_stop = threading.Event()

    # ── Registro de callbacks ──────────────────────────────────────────────

    def register_task_callback(self, tool_name: str, callback: Callable):
        """
        Registra função que sabe executar uma ferramenta agendada.

        A função recebe (ScheduledTask) e deve retornar um dict com resultado
        (ex: {"success": True, "rows_processed": 100}).
        """
        self._task_callbacks[tool_name] = callback

    # ── Gerenciamento de tarefas ───────────────────────────────────────────

    def create_task(self,
                    user_id: str,
                    tool_name: str,
                    tool_action: str,
                    input_files: List[str],
                    frequency: str,
                    time_of_day: Optional[str] = None,
                    cron_expression: Optional[str] = None,
                    **kwargs) -> ScheduledTask:
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

        if self._storage:
            try:
                self._storage.save_scheduled_task(task)
                logger.info(f"Tarefa agendada criada: {task.task_id}")
            except Exception as e:
                logger.error(f"Erro ao salvar tarefa: {e}")

        return task

    def get_tasks_for_user(self, user_id: str) -> List[ScheduledTask]:
        if not self._storage:
            return []
        try:
            raw = self._storage.get_scheduled_tasks(user_id)
            result = []
            for item in raw:
                if isinstance(item, ScheduledTask):
                    result.append(item)
                elif isinstance(item, dict):
                    try:
                        result.append(ScheduledTask.from_dict(item))
                    except Exception as e:
                        logger.warning(f"Erro ao converter tarefa agendada: {e}")
            return result
        except Exception as e:
            logger.error(f"Erro ao recuperar tarefas: {e}")
            return []

    def get_due_tasks(self, user_id: str) -> List[ScheduledTask]:
        tasks = self.get_tasks_for_user(user_id)
        return [t for t in tasks if t.should_run_now()]

    def disable_task(self, task_id: str) -> bool:
        if self._storage:
            try:
                self._storage.disable_scheduled_task(task_id)
                return True
            except Exception as e:
                logger.error(f"Erro ao desabilitar tarefa: {e}")
        return False

    def delete_task(self, task_id: str) -> bool:
        if self._storage:
            try:
                self._storage.delete_scheduled_task(task_id)
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar tarefa: {e}")
        return False

    # ── Execução via TaskExecutor ─────────────────────────────────────────

    def execute_task(self, task: ScheduledTask) -> bool:
        """
        Executa uma tarefa agendada usando o TaskExecutor unificado.
        A tarefa roda em background thread com tracking, progresso e notificações.
        """
        if task.tool_name not in self._task_callbacks:
            logger.error(f"Sem callback para ferramenta agendada: {task.tool_name}")
            return False

        callback = self._task_callbacks[task.tool_name]

        def execute_func():
            return callback(task)

        task_id, error = self._executor.submit(
            tool_name=task.tool_name,
            tool_display_name=f"{task.tool_name} (Agendada)",
            execute_func=execute_func,
            user_id=task.user_id,
        )

        if error:
            logger.error(f"Erro ao submeter tarefa agendada {task.task_id}: {error}")
            return False

        # Atualizar last_run e next_run após submeter
        task.last_run = datetime.now().isoformat()
        task.next_run = task.calculate_next_run().isoformat()

        if self._storage:
            try:
                self._storage.update_scheduled_task(task)
            except Exception as e:
                logger.error(f"Erro ao atualizar tarefa agendada: {e}")

        logger.info(f"Tarefa agendada submetida ao executor: {task.task_id} -> {task_id}")
        return True

    # ── Polling automático ────────────────────────────────────────────────

    def start_polling(self, interval_seconds: int = 60):
        """
        Inicia thread em background que verifica tarefas pendentes a cada N segundos.
        """
        if self._polling_thread and self._polling_thread.is_alive():
            logger.warning("Polling já está em execução")
            return

        self._polling_stop.clear()

        def poll_loop():
            logger.info(f"Scheduler polling iniciado (intervalo={interval_seconds}s)")
            while not self._polling_stop.is_set():
                try:
                    if self._storage:
                        all_users = self._get_all_users_with_tasks()
                        for user_id in all_users:
                            due = self.get_due_tasks(user_id)
                            for scheduled in due:
                                self.execute_task(scheduled)
                except Exception as e:
                    logger.error(f"Erro no polling do scheduler: {e}")
                self._polling_stop.wait(interval_seconds)
            logger.info("Scheduler polling encerrado")

        self._polling_thread = threading.Thread(target=poll_loop, daemon=True)
        self._polling_thread.start()

    def stop_polling(self):
        """Para a thread de polling."""
        self._polling_stop.set()
        if self._polling_thread:
            self._polling_thread.join(timeout=5)

    def _get_all_users_with_tasks(self) -> List[str]:
        """Obtém lista de user_ids que têm tarefas agendadas."""
        try:
            sql = "SELECT DISTINCT user_id FROM scheduled_tasks_local WHERE enabled = 1"
            import sqlite3
            conn = sqlite3.connect(self._storage.db_path, timeout=5)
            conn.execute("PRAGMA busy_timeout=5000")
            cursor = conn.cursor()
            cursor.execute(sql)
            users = [row[0] for row in cursor.fetchall()]
            conn.close()
            return users
        except Exception as e:
            logger.error(f"Erro ao listar users com tarefas: {e}")
            return []

    # ── Windows Task Scheduler (Enterprise) ───────────────────────────────

    def create_windows_scheduled_task(self, task: ScheduledTask, app_path: str) -> bool:
        """
        Cria tarefa no Windows Task Scheduler (Enterprise only)
        Usa o TaskExecutor para executar quando o app iniciar.
        """
        try:
            import sys as _sys
            import subprocess
            import os

            if _sys.platform != "win32":
                logger.warning("Windows Task Scheduler disponível apenas no Windows")
                return False

            task_name = f"DataMaster_{task.task_id}"

            runner_script = f"""
import sys
sys.path.insert(0, '{os.path.dirname(app_path)}')
from src.core.task_scheduler import get_task_scheduler
from src.core.tasks.task_executor import task_executor

scheduler = get_task_scheduler()
scheduler._executor = task_executor
task = scheduler.get_task('{task.task_id}')
if task:
    scheduler.execute_task(task)
            """

            script_path = os.path.join(os.environ.get('TEMP', '/tmp'), f"task_{task.task_id}.py")
            with open(script_path, 'w') as f:
                f.write(runner_script)

            ps_command = f"""
$trigger = New-ScheduledTaskTrigger -AtStartup
$action = New-ScheduledTaskAction -Execute 'python' -Argument '"{script_path}"'
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "{task_name}" -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Force
            """

            subprocess.run(
                ["powershell", "-Command", ps_command],
                check=True, capture_output=True
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
