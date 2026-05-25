"""
ExecutionHistoryManager - Gerencia histórico de execuções por ferramenta
Rastreia resultados, arquivos gerados e permite download/visualização
"""
import json
import os
import shutil
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import threading

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class ExecutionHistoryRecord:
    """Registro individual no histórico"""
    def __init__(
        self,
        task_id: str,
        tool_name: str,
        tool_display_name: str,
        status: str,
        result_data: Dict = None,
        generated_files: List[str] = None,
        logs: List[str] = None,
        duration_seconds: float = 0,
        completed_at: str = None,
        error_message: str = None
    ):
        self.task_id = task_id
        self.tool_name = tool_name
        self.tool_display_name = tool_display_name
        self.status = status
        self.result_data = result_data or {}
        self.generated_files = generated_files or []
        self.logs = logs or []
        self.duration_seconds = duration_seconds
        self.completed_at = completed_at or datetime.now().isoformat()
        self.error_message = error_message

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "tool_name": self.tool_name,
            "tool_display_name": self.tool_display_name,
            "status": self.status,
            "result_data": self.result_data,
            "generated_files": self.generated_files,
            "logs": self.logs[-100:],  # Últimas 100 linhas
            "duration_seconds": self.duration_seconds,
            "completed_at": self.completed_at,
            "error_message": self.error_message
        }

    @staticmethod
    def from_dict(data: Dict) -> "ExecutionHistoryRecord":
        return ExecutionHistoryRecord(
            task_id=data["task_id"],
            tool_name=data["tool_name"],
            tool_display_name=data["tool_display_name"],
            status=data["status"],
            result_data=data.get("result_data", {}),
            generated_files=data.get("generated_files", []),
            logs=data.get("logs", []),
            duration_seconds=data.get("duration_seconds", 0),
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message")
        )


class ExecutionHistoryManager:
    """Gerenciador de histórico de execuções"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._lock = threading.RLock()
        
        # Caminho para armazenar histórico
        self.history_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))) / ".execution_history"
        self.history_dir.mkdir(exist_ok=True)
        
        # Arquivo de índice geral
        self.index_file = self.history_dir / "index.json"
        self._load_index()

        from src.core.storage.storage_manager import StorageManager
        self._storage = StorageManager()

    RETENTION_MAP = {
        "1h": 3600,
        "7d": 604800,
        "15d": 1296000,
        "1m": 2592000,
        "6m": 15552000,
    }

    def set_retention(self, retention_key: str):
        self._storage.save_history_retention(retention_key)
        self._cleanup_old()

    def get_retention(self) -> str:
        session = self._storage.get_saved_session()
        plan = (session or {}).get("plan", "gratis")
        if plan == "gratis":
            return "1h"
        return self._storage.get_history_retention()

    def _get_retention_seconds(self, retention_key: str) -> int:
        return self.RETENTION_MAP.get(retention_key, 604800)

    @property
    def _backup_root(self) -> Path:
        return Path(config.OUTPUT_DIR) / "backups"

    def _remove_backup_files(self, record_data: dict):
        """Remove arquivos de backup vinculados a um registro expirado."""
        task_id = record_data.get("task_id", "")
        tool_name = record_data.get("tool_name", "")

        # Remove a pasta de backup inteira: outputs/backups/{tool}/{task_id}/
        if task_id and tool_name:
            backup_dir = self._backup_root / tool_name / task_id
            if backup_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)

        # Também remove arquivos individuais listados em generated_files
        for fref in record_data.get("generated_files", []):
            path = ""
            if isinstance(fref, dict):
                path = fref.get("path", "")
            elif isinstance(fref, str):
                path = fref
            if path and os.path.exists(path):
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass

    def _cleanup_old(self):
        retention_key = self.get_retention()
        max_age = self._get_retention_seconds(retention_key)
        now = datetime.now()
        deleted = 0
        for tool_dir in self.history_dir.glob("*"):
            if not tool_dir.is_dir():
                continue
            for file_path in tool_dir.glob("*.json"):
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if (now - mtime).total_seconds() > max_age:
                        # Lê o registro para obter os arquivos vinculados
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                record_data = json.load(f)
                            self._remove_backup_files(record_data)
                        except Exception:
                            pass
                        file_path.unlink()
                        deleted += 1
                except Exception:
                    pass
        if deleted:
            self._load_index()
            self._save_index()
    
    def _load_index(self):
        """Carrega índice de histórico"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            else:
                self.index = {"by_tool": {}, "all_tasks": []}
        except Exception as e:
            logger.error(f"Erro ao carregar índice: {e}")
            self.index = {"by_tool": {}, "all_tasks": []}
    
    def _save_index(self):
        """Salva índice de histórico"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar índice: {e}")
    
    def save_record(self, record: ExecutionHistoryRecord):
        """Salva um registro no histórico"""
        with self._lock:
            try:
                # Criar diretório por ferramenta
                tool_dir = self.history_dir / record.tool_name
                tool_dir.mkdir(exist_ok=True)
                
                # Salvar registro
                record_file = tool_dir / f"{record.task_id}.json"
                with open(record_file, 'w', encoding='utf-8') as f:
                    json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)
                
                # Atualizar índice
                if record.tool_name not in self.index["by_tool"]:
                    self.index["by_tool"][record.tool_name] = []
                
                self.index["by_tool"][record.tool_name].append({
                    "task_id": record.task_id,
                    "completed_at": record.completed_at,
                    "status": record.status
                })
                
                self.index["all_tasks"].append({
                    "task_id": record.task_id,
                    "tool_name": record.tool_name,
                    "tool_display_name": record.tool_display_name,
                    "completed_at": record.completed_at,
                    "status": record.status
                })
                
                self._save_index()
                
                # Limpar registros antigos conforme retenção
                self._cleanup_old()
                
            except Exception as e:
                logger.error(f"Erro ao salvar registro: {e}")
    
    def get_history_by_tool(self, tool_name: str, limit: int = 50) -> List[ExecutionHistoryRecord]:
        """Obtém histórico de uma ferramenta"""
        with self._lock:
            try:
                tool_dir = self.history_dir / tool_name
                if not tool_dir.exists():
                    return []
                
                records = []
                for file_path in sorted(tool_dir.glob("*.json"), reverse=True)[:limit]:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            records.append(ExecutionHistoryRecord.from_dict(data))
                    except Exception as e:
                        logger.error(f"Erro ao carregar {file_path}: {e}")
                
                return records
            except Exception as e:
                logger.error(f"Erro ao obter histórico: {e}")
                return []
    
    def get_all_history(self, limit: int = 100) -> List[ExecutionHistoryRecord]:
        """Obtém histórico de todas as ferramentas"""
        with self._lock:
            try:
                records = []
                for tool_dir in sorted(self.history_dir.glob("*"), key=lambda x: x.is_dir()):
                    if not tool_dir.is_dir():
                        continue
                    for file_path in sorted(tool_dir.glob("*.json"), reverse=True):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                records.append(ExecutionHistoryRecord.from_dict(data))
                        except Exception as e:
                            logger.error(f"Erro ao carregar {file_path}: {e}")
                        
                        if len(records) >= limit:
                            return records[:limit]
                
                return records
            except Exception as e:
                logger.error(f"Erro ao obter histórico geral: {e}")
                return []
    
    def get_record(self, tool_name: str, task_id: str) -> Optional[ExecutionHistoryRecord]:
        """Obtém registro específico"""
        with self._lock:
            try:
                tool_dir = self.history_dir / tool_name
                file_path = tool_dir / f"{task_id}.json"
                
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return ExecutionHistoryRecord.from_dict(data)
            except Exception as e:
                logger.error(f"Erro ao obter registro: {e}")
            
            return None
    
    def add_generated_file(self, tool_name: str, task_id: str, file_path: str):
        """Registra um arquivo gerado pela ferramenta"""
        with self._lock:
            try:
                record = self.get_record(tool_name, task_id)
                if record:
                    # Armazenar informações do arquivo
                    if os.path.exists(file_path):
                        file_info = {
                            "path": file_path,
                            "name": os.path.basename(file_path),
                            "size": os.path.getsize(file_path),
                            "created_at": datetime.now().isoformat()
                        }
                        record.generated_files.append(file_info)
                        
                        # Salvar atualização
                        tool_dir = self.history_dir / tool_name
                        record_file = tool_dir / f"{task_id}.json"
                        with open(record_file, 'w', encoding='utf-8') as f:
                            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Erro ao registrar arquivo: {e}")
    
    def download_file(self, tool_name: str, task_id: str, file_name: str, destination: str) -> bool:
        """Baixa um arquivo gerado"""
        try:
            record = self.get_record(tool_name, task_id)
            if not record:
                return False
            
            # Localizar arquivo
            for file_info in record.generated_files:
                if file_info["name"] == file_name:
                    src_path = file_info["path"]
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, destination)
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo: {e}")
            return False
    
    def get_tool_statistics(self, tool_name: str) -> Dict:
        """Obtém estatísticas de uma ferramenta"""
        try:
            history = self.get_history_by_tool(tool_name, limit=1000)
            
            total = len(history)
            completed = sum(1 for r in history if r.status == "completed")
            failed = sum(1 for r in history if r.status == "failed")
            cancelled = sum(1 for r in history if r.status == "cancelled")
            avg_duration = sum(r.duration_seconds for r in history) / len(history) if history else 0
            total_files = sum(len(r.generated_files) for r in history)
            
            return {
                "total_executions": total,
                "completed": completed,
                "failed": failed,
                "cancelled": cancelled,
                "success_rate": (completed / total * 100) if total > 0 else 0,
                "average_duration_seconds": avg_duration,
                "total_files_generated": total_files
            }
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}
    
    def clear_history(self, tool_name: str = None, days_old: int = None) -> int:
        """Limpa histórico (por ferramenta ou por idade) e remove backups vinculados."""
        try:
            deleted = 0
            
            if tool_name:
                tool_dir = self.history_dir / tool_name
                if tool_dir.exists():
                    for file_path in tool_dir.glob("*.json"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                self._remove_backup_files(json.load(f))
                        except Exception:
                            pass
                        os.remove(file_path)
                        deleted += 1
                    # Remove pasta de backup da ferramenta inteira
                    backup_tool = self._backup_root / tool_name
                    if backup_tool.exists():
                        shutil.rmtree(backup_tool, ignore_errors=True)
            else:
                for file_path in self.history_dir.glob("*/*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            self._remove_backup_files(json.load(f))
                    except Exception:
                        pass
                    os.remove(file_path)
                    deleted += 1
                # Remove todos os backups
                if self._backup_root.exists():
                    shutil.rmtree(self._backup_root, ignore_errors=True)
            
            # Reconstruir índice
            self._load_index()
            self._save_index()
            
            return deleted
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
            return 0


def get_history_manager() -> ExecutionHistoryManager:
    """Obtém instância singleton do HistoryManager"""
    return ExecutionHistoryManager()
