"""
Data Export - Exportação de dados do usuário (LGPD compliance)
Atende ao Artigo 18(V) da LGPD - direito à portabilidade de dados.
"""
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional
from src.core.audit_logger import audit_lgpd_export

log = logging.getLogger(__name__)


class DataExport:
    """Exporta todos os dados do usuário do SQLite local."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def export_user_data(self, user_id: str) -> Optional[dict]:
        """Exporta todos os dados do usuário em formato JSON.
        
        Args:
            user_id: ID do usuário no Supabase
            
        Returns:
            Dict com todos os dados do usuário, ou None em caso de erro
        """
        if not user_id:
            log.error("user_id não fornecido")
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            export_data = {
                "export_info": {
                    "user_id": user_id,
                    "export_date": datetime.now().isoformat(),
                    "format": "datamaster_pro_export_v1",
                    "application": "DataMaster Pro"
                },
                "profile": self._export_profile(cursor, user_id),
                "tasks": self._export_tasks(cursor, user_id),
                "executions": self._export_executions(cursor, user_id),
                "execution_logs": self._export_execution_logs(cursor, user_id),
                "scheduled_tasks": self._export_scheduled_tasks(cursor, user_id),
                "tool_configurations": self._export_tool_configs(cursor, user_id),
                "settings": self._export_settings(cursor, user_id),
            }
            
            conn.close()
            
            # Redact dados sensíveis
            export_data = self._redact_sensitive(export_data)
            
            log.info("Exportação concluída para usuário: %s", user_id)
            total_records = sum(
                len(v) if isinstance(v, list) else (1 if v else 0)
                for v in export_data.values() if isinstance(v, (list, dict))
            )
            audit_lgpd_export(user_id, total_records, "json")
            return export_data
            
        except Exception as e:
            log.error("Erro ao exportar dados: %s", e)
            return None
    
    def export_to_file(self, user_id: str, output_path: str) -> bool:
        """Exporta dados para um arquivo JSON.
        
        Args:
            user_id: ID do usuário
            output_path: Caminho do arquivo de saída
            
        Returns:
            True se exportado com sucesso
        """
        data = self.export_user_data(user_id)
        if not data:
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log.info("Dados exportados para: %s", output_path)
            return True
        except Exception as e:
            log.error("Erro ao salvar arquivo de exportação: %s", e)
            return False
    
    def _export_profile(self, cursor, user_id: str) -> dict:
        """Exporta perfil do usuário."""
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {}
    
    def _export_tasks(self, cursor, user_id: str) -> list:
        """Exporta todas as tarefas do usuário."""
        cursor.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def _export_executions(self, cursor, user_id: str) -> list:
        """Exporta histórico de execuções."""
        cursor.execute("SELECT * FROM executions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def _export_execution_logs(self, cursor, user_id: str) -> list:
        """Exporta logs detalhados de execuções."""
        try:
            cursor.execute("SELECT * FROM execution_logs_local WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []
    
    def _export_scheduled_tasks(self, cursor, user_id: str) -> list:
        """Exporta tarefas agendadas."""
        try:
            cursor.execute("SELECT * FROM scheduled_tasks_local WHERE user_id = ?", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []
    
    def _export_tool_configs(self, cursor, user_id: str) -> list:
        """Exporta configurações das ferramentas."""
        try:
            cursor.execute("SELECT * FROM tool_configurations_local WHERE user_id = ?", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def _export_settings(self, cursor, user_id: str) -> dict:
        """Exporta preferências do usuário."""
        try:
            cursor.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            return {row['key']: row['value'] for row in rows} if rows else {}
        except Exception:
            return {}
    
    def _redact_sensitive(self, data: dict) -> dict:
        """Remove dados sensíveis da exportação."""
        # Redact no perfil
        if data.get("profile"):
            for key in ["session_token_encrypted", "refresh_token_encrypted", "hwid"]:
                if key in data["profile"]:
                    data["profile"][key] = "***REDACTED***"
        
        # Redact nas tasks (parâmetros podem conter dados sensíveis)
        for task in data.get("tasks", []):
            if "input_files" in task:
                task["input_files"] = "[REDACTED_FILE_PATHS]"
        
        return data
