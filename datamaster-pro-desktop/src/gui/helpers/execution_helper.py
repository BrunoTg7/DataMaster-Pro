"""
ExecutionHelper - Integração entre ToolPage e TaskExecutor
Fornece métodos helpers para ferramentas criarem e monitorarem tarefas
Integra com histórico de execução para rastreamento de resultados e arquivos
"""
import logging
import os
import time
import config
from pathlib import Path
from typing import Optional, Callable, Dict, List

log = logging.getLogger(__name__)
from src.core.tasks.task_executor import task_executor
from src.core.tasks.execution_history_manager import get_history_manager, ExecutionHistoryRecord


class ExecutionHelper:
    """Helper para facilitar integração de ferramentas com TaskExecutor"""

    def __init__(self, tool_key: str, tool_display_name: str, user_id: str = None):
        self.tool_key = tool_key
        self.tool_display_name = tool_display_name
        self.user_id = user_id
        self._executor = task_executor
        self.task_id = None
        self._start_time = None

    def create_task(self, on_progress: Callable = None, on_log: Callable = None) -> tuple[Optional[str], Optional[str]]:
        """Cria uma nova tarefa de execução"""
        task_id, error = self._executor.create_task(
            tool_name=self.tool_key,
            tool_display_name=self.tool_display_name,
            input_params={},
            progress_callback=on_progress,
            log_callback=on_log,
        )

        if task_id:
            self.task_id = task_id
            self._start_time = time.time()

        return task_id, error

    def update_progress(self, percent: int, message: str = ""):
        """Atualiza progresso da tarefa"""
        if self.task_id:
            self._executor.update_progress(self.task_id, percent, message)

    def add_log(self, message: str):
        """Adiciona mensagem de log"""
        if self.task_id:
            self._executor.add_log(self.task_id, message)

    def complete(self, result_data: Dict = None, generated_files: List[str] = None):
        """Marca tarefa como concluída"""
        if self.task_id:
            log.debug("complete() task_id=%s", self.task_id)
            task = self._executor.get_task(self.task_id)
            if task:
                self._executor.complete_task(
                    self.task_id,
                    output_path=task.get("output_path", ""),
                    rows=task.get("rows_processed", 0),
                    hours=task.get("hours_saved", 0),
                )
            else:
                self._executor.complete_task(self.task_id)
            log.debug("complete_task done, saving to history...")
            self.save_to_history(
                status="completed",
                result_data=result_data,
                generated_files=generated_files,
            )
            log.debug("save_to_history done")
        else:
            log.debug("complete() skipped: no task_id")

    def fail(self, error: str):
        """Marca tarefa como falhou"""
        if self.task_id:
            self._executor.fail_task(self.task_id, error)
            self.save_to_history(
                status="failed",
                error_message=error,
            )

    def cancel(self):
        """Cancela tarefa"""
        if self.task_id:
            self._executor.cancel_task(self.task_id)

    def is_cancelled(self) -> bool:
        """Verifica se tarefa foi cancelada"""
        if not self.task_id:
            return False
        task = self._executor.get_task(self.task_id)
        return task is not None and task.get("status") == "cancelled"

    def get_duration_seconds(self) -> float:
        """Retorna tempo decorrido em segundos"""
        if self._start_time:
            return time.time() - self._start_time
        return 0.0

    def get_task(self) -> Optional[dict]:
        """Obtém dados da tarefa atual (dict)"""
        if self.task_id:
            return self._executor.get_task(self.task_id)
        return None

    # ============ HISTÓRICO ============

    def register_generated_file(self, file_path: str):
        """Registra um arquivo gerado pela ferramenta"""
        if self.task_id:
            history = get_history_manager()
            history.add_generated_file(self.tool_key, self.task_id, file_path)

    def get_history(self, limit: int = 50) -> List[ExecutionHistoryRecord]:
        """Obtém histórico de execução desta ferramenta"""
        history = get_history_manager()
        return history.get_history_by_tool(self.tool_key, limit)

    def get_statistics(self) -> Dict:
        """Obtém estatísticas desta ferramenta"""
        history = get_history_manager()
        return history.get_tool_statistics(self.tool_key)

    def _backup_file(self, src_path: str) -> str:
        """Copia arquivo gerado para dentro do sistema (backup) e retorna novo path."""
        if not src_path or not os.path.isfile(src_path):
            return src_path
        backup_dir = Path(config.OUTPUT_DIR) / "backups" / self.tool_key / (self.task_id or "unknown")
        backup_dir.mkdir(parents=True, exist_ok=True)
        dst = backup_dir / os.path.basename(src_path)
        try:
            import shutil
            shutil.copy2(src_path, str(dst))
            log.info("Backup: %s -> %s", src_path, dst)
            return str(dst)
        except Exception as e:
            log.error("Erro ao copiar backup: %s", e)
            return src_path

    def _fmt_file(self, path: str) -> dict:
        """Converte caminho de arquivo em dict com metadados."""
        import os
        backup_path = self._backup_file(path)
        return {
            "path": backup_path,
            "name": os.path.basename(path),
            "size": os.path.getsize(backup_path) if os.path.isfile(backup_path) else 0,
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }

    def save_to_history(self, status: str, result_data: Dict = None,
                        generated_files: List[str] = None, logs: List[str] = None,
                        error_message: str = None):
        """Salva execução no histórico (chamado automaticamente por complete/fail)"""
        if self.task_id:
            task = self._executor.get_task(self.task_id)
            if task:
                duration = self.get_duration_seconds()

                files = []
                for f in (generated_files or []):
                    if isinstance(f, str):
                        files.append(self._fmt_file(f))
                    else:
                        files.append(f)

                record = ExecutionHistoryRecord(
                    task_id=self.task_id,
                    tool_name=self.tool_key,
                    tool_display_name=self.tool_display_name,
                    status=status,
                    result_data=result_data or task.get("result_data", {}),
                    generated_files=files,
                    logs=logs or task.get("log_messages", []),
                    duration_seconds=duration,
                    error_message=error_message,
                )

                history = get_history_manager()
                history.save_record(record)
