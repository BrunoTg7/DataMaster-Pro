"""
Application Services - Use cases orquestrando domínio e infraestrutura
Cada serviço representa um caso de uso da aplicação.
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime

from src.domain.entities import Task, TaskStatus, User, PlanType, Execution
from src.domain.interfaces import (
    ITaskRepository, IExecutionRepository, IUserRepository,
    ISyncQueue, ISyncProvider, ICacheProvider, IEventBus,
)

log = logging.getLogger(__name__)


class SubmitTaskUseCase:
    """Use Case: Submeter uma tarefa para execução."""

    def __init__(
        self,
        task_repo: ITaskRepository,
        user_repo: IUserRepository,
        event_bus: IEventBus,
    ):
        self._task_repo = task_repo
        self._user_repo = user_repo
        self._event_bus = event_bus

    def execute(
        self,
        tool_name: str,
        tool_display_name: str,
        input_params: Dict,
        user_id: str = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """Executa o use case de submissão de tarefa.

        Returns:
            (task_id, error_message)
        """
        # Verificar se já existe tarefa rodando para esta ferramenta
        running = self._task_repo.get_running_task_by_tool(tool_name)
        if running:
            return None, f"Uma tarefa de {tool_display_name} já está em execução"

        # Criar entidade Task
        task_id = str(__import__("uuid").uuid4())
        now = datetime.now().isoformat()

        task = Task(
            id=task_id,
            tool_name=tool_name,
            tool_display_name=tool_display_name,
            user_id=user_id or "",
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            input_params=str(input_params),
        )

        # Persistir
        self._task_repo.save_task({
            "id": task.id,
            "tool_name": task.tool_name,
            "tool_display_name": task.tool_display_name,
            "user_id": task.user_id,
            "status": task.status.value,
            "progress_percent": 0,
            "progress_message": "Aguardando...",
            "error_message": "",
            "rows_processed": 0,
            "hours_saved": 0,
            "output_path": "",
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": "",
            "input_params": task.input_params,
            "log_text": "",
            "log_messages": "[]",
            "result_data": "{}",
        })

        # Publicar evento
        self._event_bus.publish("task.created", {"task_id": task_id, "tool": tool_name})

        log.info("Tarefa criada: %s (tool=%s)", task_id[:8], tool_name)
        return task_id, None


class CompleteTaskUseCase:
    """Use Case: Marcar tarefa como concluída."""

    def __init__(
        self,
        task_repo: ITaskRepository,
        execution_repo: IExecutionRepository,
        event_bus: IEventBus,
    ):
        self._task_repo = task_repo
        self._execution_repo = execution_repo
        self._event_bus = event_bus

    def execute(
        self,
        task_id: str,
        output_path: str = "",
        rows: int = 0,
        hours: float = 0,
    ):
        now = datetime.now().isoformat()
        self._task_repo.update_task(task_id, {
            "status": TaskStatus.COMPLETED.value,
            "progress_percent": 100,
            "progress_message": "Concluído",
            "output_path": output_path,
            "rows_processed": rows,
            "hours_saved": hours,
            "completed_at": now,
            "updated_at": now,
        })

        # Salvar execução
        task = self._task_repo.get_task(task_id)
        if task:
            execution = Execution(
                user_id=task.get("user_id", ""),
                tool_name=task.get("tool_name", ""),
                output_path=output_path,
                rows_processed=rows,
                hours_saved=hours,
                created_at=now,
            )
            self._execution_repo.save_execution(execution)

        self._event_bus.publish("task.completed", {"task_id": task_id, "rows": rows})
        log.info("Tarefa concluída: %s (%d linhas)", task_id[:8], rows)


class SyncUserDataUseCase:
    """Use Case: Sincronizar dados do usuário com o servidor."""

    def __init__(
        self,
        sync_queue: ISyncQueue,
        sync_provider: ISyncProvider,
        execution_repo: IExecutionRepository,
        user_repo: IUserRepository,
        cache: ICacheProvider,
        event_bus: IEventBus,
    ):
        self._sync_queue = sync_queue
        self._sync_provider = sync_provider
        self._execution_repo = execution_repo
        self._user_repo = user_repo
        self._cache = cache
        self._event_bus = event_bus

    def execute(self) -> Dict:
        """Executa sincronização completa (upload + download)."""
        if not self._sync_provider.is_connected():
            return {"success": False, "error": "Sem conexão", "offline": True}

        results = {"synced": 0, "failed": 0}

        # Upload
        pending = self._sync_queue.get_pending()
        for item in pending:
            try:
                import json
                data = json.loads(item.data_json) if isinstance(item.data_json, str) else item.data_json
                self._sync_provider.upload(item.table_name, data)
                self._sync_queue.mark_synced(item.id)
                results["synced"] += 1
            except Exception as e:
                log.error("Sync upload erro: %s", e)
                self._sync_queue.mark_failed(item.id)
                results["failed"] += 1

        # Download
        user = self._user_repo.get_session()
        if user and user.get("id"):
            try:
                remote = self._sync_provider.download("execucoes", user["id"])
                if remote:
                    self._execution_repo.replace_user_executions(user["id"], remote)
                    log.info("Sync download: %d registros", len(remote))
            except Exception as e:
                log.error("Sync download erro: %s", e)

        # Limpar fila
        self._sync_queue.cleanup()

        # Invalidar cache
        self._cache.clear(prefix="stats:")

        self._event_bus.publish("sync.completed", results)
        return {"success": results["failed"] == 0, **results}


class GetUserStatsUseCase:
    """Use Case: Obter estatísticas do usuário."""

    def __init__(
        self,
        execution_repo: IExecutionRepository,
        cache: ICacheProvider,
    ):
        self._execution_repo = execution_repo
        self._cache = cache

    def execute(self, user_id: str) -> Dict:
        cache_key = f"stats:{user_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        executions = self._execution_repo.get_executions(user_id, limit=2000)
        total_lines = total_hours = total_execs = 0
        stats_by_tool = {}

        for ex in executions:
            tool = ex.get("tool_name", "unknown")
            if tool not in stats_by_tool:
                stats_by_tool[tool] = {"execs": 0, "lines": 0}
            stats_by_tool[tool]["execs"] += 1
            stats_by_tool[tool]["lines"] += ex.get("rows_processed", 0)
            total_lines += ex.get("rows_processed", 0)
            total_hours += ex.get("hours_saved", 0)
            total_execs += 1

        result = {
            "total_lines": total_lines,
            "total_hours": total_hours,
            "total_executions": total_execs,
            "by_tool": stats_by_tool,
        }

        self._cache.set(cache_key, result, ttl=30)
        return result
