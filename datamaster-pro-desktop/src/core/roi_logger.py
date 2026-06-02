"""
ROI Manager - Rastreia execuções, calcula ROI e sincroniza com cloud
"""
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

# Tempo médio estimado para processamento manual (em segundos)
MANUAL_PROCESSING_TIME = {
    "consolidador": 180,  # 3 min por consolidação manual
    "categorizador": 120,  # 2 min por categorização manual
    "minerador": 240,     # 4 min por mineração manual
    "conciliador": 300,   # 5 min por conciliação manual
    "orcamentos": 60,     # 1 min por orçamento manual
    "data_sanitizer": 150, # 2.5 min por limpeza manual
    "validador": 90,      # 1.5 min por validação manual
}


@dataclass
class ExecutionLog:
    """Representa um log de execução"""
    execution_id: str
    user_id: str
    tool_name: str
    timestamp: str
    duration_seconds: float
    lines_processed: int
    file_size_bytes: int
    status: str  # 'success', 'failed', 'cancelled'
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Cria a partir de dicionário"""
        return cls(**data)
    
    def calculate_time_saved(self, tool_name: str) -> float:
        """
        Calcula tempo economizado em minutos
        """
        if self.status != 'success':
            return 0
        
        manual_time = MANUAL_PROCESSING_TIME.get(tool_name, 120)
        time_saved_seconds = manual_time - self.duration_seconds
        
        # Se automaçao levou mais tempo que manual, não houve economia
        if time_saved_seconds < 0:
            return 0
        
        return time_saved_seconds / 60  # Converter para minutos
    
    def calculate_roi_percentage(self, tool_name: str) -> float:
        """
        Calcula ROI em percentual
        100% = ferramente foi tão rápida quanto manual
        200% = ferramente foi 2x mais rápida
        """
        if self.status != 'success':
            return 0
        
        manual_time = MANUAL_PROCESSING_TIME.get(tool_name, 120)
        if manual_time == 0:
            return 0
        
        return ((manual_time - self.duration_seconds) / manual_time) * 100


class ROIManager:
    """
    Gerencia logs de execução e cálculo de ROI
    Suporta armazenamento local (SQLite) e sincronização com cloud
    """
    
    def __init__(self, storage_manager=None, cloud_client=None):
        """
        Args:
            storage_manager: Gerenciador de storage local (SQLite)
            cloud_client: Cliente cloud para sync
        """
        self._storage = storage_manager
        self._cloud = cloud_client
        self._pending_syncs: List[ExecutionLog] = []
    
    def log_execution(self, 
                     user_id: str,
                     tool_name: str,
                     duration_seconds: float,
                     lines_processed: int,
                     file_size_bytes: int,
                     status: str = "success",
                     error_message: Optional[str] = None) -> ExecutionLog:
        """
        Registra uma execução
        
        Returns:
            ExecutionLog criado
        """
        import uuid
        
        execution_log = ExecutionLog(
            execution_id=str(uuid.uuid4()),
            user_id=user_id,
            tool_name=tool_name,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration_seconds,
            lines_processed=lines_processed,
            file_size_bytes=file_size_bytes,
            status=status,
            error_message=error_message
        )
        
        # Salvar localmente
        if self._storage:
            try:
                self._storage.save_execution_log(execution_log)
                logger.info(f"Log de execução salvo: {execution_log.execution_id}")
            except Exception as e:
                logger.error(f"Erro ao salvar log: {e}")
        
        # Adicionar à fila de sincronização
        self._pending_syncs.append(execution_log)
        
        return execution_log
    
    def get_execution_logs(self, user_id: str, days: int = 7) -> List[ExecutionLog]:
        """
        Recupera logs de execução
        
        Args:
            user_id: ID do usuário
            days: Últimos N dias (padrão 7)
            
        Returns:
            Lista de ExecutionLog
        """
        if not self._storage:
            return []
        
        try:
            return self._storage.get_execution_logs(user_id, days)
        except Exception as e:
            logger.error(f"Erro ao recuperar logs: {e}")
            return []
    
    def get_roi_summary(self, user_id: str, days: int = 7) -> Dict:
        """
        Calcula resumo de ROI
        
        Args:
            user_id: ID do usuário
            days: Período em dias
            
        Returns:
            Dicionário com métricas de ROI
        """
        logs = self.get_execution_logs(user_id, days)
        
        if not logs:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "total_lines_processed": 0,
                "total_time_saved_minutes": 0,
                "total_manual_time_minutes": 0,
                "average_roi_percentage": 0,
                "by_tool": {}
            }
        
        successful_logs = [l for l in logs if l.status == 'success']
        total_time_saved = sum(l.calculate_time_saved(l.tool_name) for l in successful_logs)
        total_manual_time = sum(
            MANUAL_PROCESSING_TIME.get(l.tool_name, 120) / 60 
            for l in successful_logs
        )
        
        # Agrupar por ferramenta
        by_tool = {}
        for log in successful_logs:
            if log.tool_name not in by_tool:
                by_tool[log.tool_name] = {
                    "executions": 0,
                    "lines_processed": 0,
                    "time_saved_minutes": 0,
                    "avg_duration_seconds": 0
                }
            
            by_tool[log.tool_name]["executions"] += 1
            by_tool[log.tool_name]["lines_processed"] += log.lines_processed
            by_tool[log.tool_name]["time_saved_minutes"] += log.calculate_time_saved(log.tool_name)
            by_tool[log.tool_name]["avg_duration_seconds"] += log.duration_seconds
        
        # Calcular média de duração
        for tool, data in by_tool.items():
            if data["executions"] > 0:
                data["avg_duration_seconds"] /= data["executions"]
        
        avg_roi = (
            sum(l.calculate_roi_percentage(l.tool_name) for l in successful_logs) / len(successful_logs)
            if successful_logs else 0
        )
        
        return {
            "total_executions": len(logs),
            "successful_executions": len(successful_logs),
            "total_lines_processed": sum(l.lines_processed for l in successful_logs),
            "total_time_saved_minutes": round(total_time_saved, 2),
            "total_manual_time_minutes": round(total_manual_time, 2),
            "average_roi_percentage": round(avg_roi, 2),
            "by_tool": by_tool
        }
    
    def sync_to_cloud(self) -> bool:
        """
        Sincroniza logs pendentes com cloud (Supabase)
        
        Returns:
            True se sincronização bem-sucedida
        """
        if not self._cloud or not self._pending_syncs:
            return True  # Sem cloud é ok, logs estão localmente
        
        try:
            logs_to_sync = [log.to_dict() for log in self._pending_syncs]
            
            self._cloud.table("execution_logs").insert(logs_to_sync).execute()
            
            logger.info(f"{len(logs_to_sync)} logs sincronizados com cloud")
            self._pending_syncs.clear()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar com cloud: {e}")
            return False
    
    def get_cloud_logs(self, user_id: str) -> Optional[List[ExecutionLog]]:
        """
        Recupera logs do cloud
        """
        if not self._cloud:
            return None
        
        try:
            response = (
                self._cloud.table("execution_logs")
                .select("*")
                .eq("user_id", user_id)
                .order("timestamp", desc=True)
                .execute()
            )
            
            return [ExecutionLog.from_dict(item) for item in response.data] if response.data else []
            
        except Exception as e:
            logger.error(f"Erro ao recuperar logs do cloud: {e}")
            return None


# Singleton
_roi_manager_instance: Optional[ROIManager] = None


def get_roi_manager(storage_manager=None, cloud_client=None) -> ROIManager:
    """Factory para obter instância do ROI Manager"""
    global _roi_manager_instance
    
    if _roi_manager_instance is None:
        _roi_manager_instance = ROIManager(storage_manager, cloud_client)
    
    return _roi_manager_instance
