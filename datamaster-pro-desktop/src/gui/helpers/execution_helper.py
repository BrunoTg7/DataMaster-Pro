"""
ExecutionManagerIntegration - Integração entre ToolPage e ExecutionManager
Fornece métodos helpers para ferramentas criarem e monitorarem tarefas
Integra com histórico de execução para rastreamento de resultados e arquivos
"""
import time
import threading
from typing import Optional, Callable, Dict, List
from src.core.tasks.execution_manager import get_execution_manager, ExecutionState
from src.core.tasks.execution_history_manager import get_history_manager, ExecutionHistoryRecord


class ExecutionHelper:
    """Helper para facilitar integração de ferramentas com ExecutionManager"""
    
    def __init__(self, tool_key: str, tool_display_name: str, user_id: str = None):
        self.tool_key = tool_key
        self.tool_display_name = tool_display_name
        self.user_id = user_id
        self.manager = get_execution_manager()
        self.task_id = None
        self._start_time = None
    
    def create_task(self, on_progress: Callable = None, on_log: Callable = None) -> tuple[Optional[str], Optional[str]]:
        """Cria uma nova tarefa de execução"""
        task_id, error = self.manager.create_task(
            tool_name=self.tool_key,
            tool_display_name=self.tool_display_name,
            user_id=self.user_id,
            progress_callback=on_progress,
            log_callback=on_log
        )
        
        if task_id:
            self.task_id = task_id
            self._start_time = time.time()
        
        return task_id, error
    
    def update_progress(self, percent: int, message: str = ""):
        """Atualiza progresso da tarefa"""
        if self.task_id:
            self.manager.update_progress(self.task_id, percent, message)
    
    def add_log(self, message: str):
        """Adiciona mensagem de log"""
        if self.task_id:
            self.manager.add_log(self.task_id, message)
    
    def complete(self, result_data: Dict = None, generated_files: List[str] = None):
        """Marca tarefa como concluída"""
        if self.task_id:
            print(f"[ExecutionHelper] complete() task_id={self.task_id}")
            self.manager.complete_task(self.task_id, result_data)
            print("[ExecutionHelper] complete_task done, saving to history...")
            # Salvar automaticamente no histórico
            self.save_to_history(
                status="completed",
                result_data=result_data,
                generated_files=generated_files
            )
            print("[ExecutionHelper] save_to_history done")
        else:
            print("[ExecutionHelper] complete() skipped: no task_id")
    
    def fail(self, error: str):
        """Marca tarefa como falhou"""
        if self.task_id:
            self.manager.fail_task(self.task_id, error)
            # Salvar automaticamente no histórico
            self.save_to_history(
                status="failed",
                error_message=error
            )
    
    def cancel(self):
        """Cancela tarefa"""
        if self.task_id:
            self.manager.cancel_task(self.task_id)
    
    def is_cancelled(self) -> bool:
        """Verifica se tarefa foi cancelada"""
        if not self.task_id:
            return False
        task = self.manager.get_task(self.task_id)
        return task and task.status == ExecutionState.CANCELLED
    
    def get_duration_seconds(self) -> float:
        """Retorna tempo decorrido em segundos"""
        if self._start_time:
            return time.time() - self._start_time
        return 0.0
    
    def get_task(self):
        """Obtém objeto da tarefa atual"""
        if self.task_id:
            return self.manager.get_task(self.task_id)
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
    
    def _fmt_file(self, path: str) -> dict:
        """Converte caminho de arquivo em dict com metadados."""
        import os
        return {
            "path": path,
            "name": os.path.basename(path),
            "size": os.path.getsize(path) if os.path.isfile(path) else 0,
            "created_at": __import__("datetime").datetime.now().isoformat()
        }

    def save_to_history(self, status: str, result_data: Dict = None, 
                       generated_files: List[str] = None, logs: List[str] = None,
                       error_message: str = None):
        """Salva execução no histórico (chamado automaticamente por complete/fail)"""
        if self.task_id:
            task = self.manager.get_task(self.task_id)
            if task:
                duration = self.get_duration_seconds()

                # Converte paths string para dicts com metadados
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
                    result_data=result_data or task.result_data,
                    generated_files=files,
                    logs=logs or task.log_messages,
                    duration_seconds=duration,
                    error_message=error_message
                )
                
                history = get_history_manager()
                history.save_record(record)
