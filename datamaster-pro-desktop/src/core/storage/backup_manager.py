"""
Database Backup Manager - Backup e recuperação do SQLite local
"""
import os
import shutil
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional
import threading

log = logging.getLogger(__name__)


class BackupManager:
    """Gerencia backups do banco de dados SQLite local.
    
    Funcionalidades:
    - Backup incremental antes de operações críticas
    - Rotação automática de backups (mantém últimos N)
    - Verificação de integridade do banco
    - Restauração a partir de backup
    """
    
    def __init__(self, db_path: str, backup_dir: str = None, max_backups: int = 5):
        self.db_path = db_path
        self.backup_dir = backup_dir or os.path.join(os.path.dirname(db_path), "backups")
        self.max_backups = max_backups
        self._backup_lock = threading.Lock()
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, label: str = None) -> Optional[str]:
        """Cria um backup do banco de dados.
        
        Args:
            label: Rótulo opcional para identificar o backup
            
        Returns:
            Caminho do backup criado, ou None em caso de erro
        """
        if not os.path.exists(self.db_path):
            log.warning("Banco de dados não encontrado: %s", self.db_path)
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        backup_name = f"datamaster_backup{suffix}_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        with self._backup_lock:
            try:
                # Usar backup do SQLite para consistência
                source = sqlite3.connect(self.db_path)
                dest = sqlite3.connect(backup_path)
                source.backup(dest)
                dest.close()
                source.close()
                
                log.info("Backup criado: %s", backup_path)
                self._rotate_backups()
                return backup_path
            except Exception as e:
                log.error("Erro ao criar backup: %s", e)
                # Fallback: cópia simples
                try:
                    shutil.copy2(self.db_path, backup_path)
                    log.info("Backup (cópia simples) criado: %s", backup_path)
                    self._rotate_backups()
                    return backup_path
                except Exception as e2:
                    log.error("Erro no backup fallback: %s", e2)
                    return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restaura o banco a partir de um backup.
        
        Args:
            backup_path: Caminho do backup a ser restaurado
            
        Returns:
            True se restaurado com sucesso
        """
        if not os.path.exists(backup_path):
            log.error("Backup não encontrado: %s", backup_path)
            return False
        
        if not self.verify_integrity(backup_path):
            log.error("Backup falhou na verificação de integridade: %s", backup_path)
            return False
        
        with self._backup_lock:
            try:
                # Criar backup do estado atual antes de restaurar
                self.create_backup(label="pre_restore")
                
                shutil.copy2(backup_path, self.db_path)
                log.info("Banco restaurado a partir de: %s", backup_path)
                return True
            except Exception as e:
                log.error("Erro ao restaurar backup: %s", e)
                return False
    
    def verify_integrity(self, db_path: str = None) -> bool:
        """Verifica integridade do banco de dados.
        
        Args:
            db_path: Caminho do banco (usa self.db_path se None)
            
        Returns:
            True se o banco estiver íntegro
        """
        target = db_path or self.db_path
        if not os.path.exists(target):
            return False
        
        try:
            conn = sqlite3.connect(target)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return result[0] == "ok"
        except Exception as e:
            log.error("Erro na verificação de integridade: %s", e)
            return False
    
    def list_backups(self) -> list[dict]:
        """Lista backups disponíveis ordenados por data (mais recente primeiro)."""
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups
        
        for f in os.listdir(self.backup_dir):
            if f.endswith(".db"):
                path = os.path.join(self.backup_dir, f)
                stat = os.stat(path)
                backups.append({
                    "name": f,
                    "path": path,
                    "size_mb": stat.st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    def _rotate_backups(self):
        """Remove backups antigos mantendo apenas max_backups"""
        backups = self.list_backups()
        if len(backups) > self.max_backups:
            for old in backups[self.max_backups:]:
                try:
                    os.remove(old["path"])
                    log.info("Backup antigo removido: %s", old["name"])
                except OSError as e:
                    log.warning("Erro ao remover backup antigo %s: %s", old["name"], e)
    
    def auto_backup(self, interval_hours: int = 24) -> Optional[str]:
        """Cria backup automático se o último backup for mais antigo que interval_hours."""
        backups = self.list_backups()
        if backups:
            last_backup = datetime.fromisoformat(backups[0]["created"])
            if datetime.now() - last_backup < timedelta(hours=interval_hours):
                return None
        
        return self.create_backup(label="auto")
