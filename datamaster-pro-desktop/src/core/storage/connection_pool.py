"""
SQLite Connection Pool - Gerencia conexões SQLite de forma eficiente
Evita criar múltiplas conexões simultâneas e reduz overhead.
"""
import sqlite3
import threading
import logging
import os
from contextlib import contextmanager

log = logging.getLogger(__name__)


class SQLiteConnectionPool:
    """Pool singleton de conexões SQLite com WAL mode e busy_timeout.
    
    Uso:
        pool = SQLiteConnectionPool.get_instance(db_path)
        with pool.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str, max_connections: int = 3):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections: list[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()
        self._active_count = 0

    @classmethod
    def get_instance(cls, db_path: str = None) -> "SQLiteConnectionPool":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if db_path is None:
                        raise ValueError("db_path é obrigatório na primeira chamada")
                    cls._instance = cls(db_path)
        return cls._instance

    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    @contextmanager
    def connection(self):
        """Context manager que fornece uma conexão do pool.
        
        Se o pool estiver cheio, espera até que uma conexão seja liberada.
        """
        conn = None
        with self._pool_lock:
            if self._connections:
                conn = self._connections.pop()
                self._active_count += 1
            elif self._active_count < self.max_connections:
                self._active_count += 1
                try:
                    conn = self._create_connection()
                except Exception:
                    self._active_count -= 1
                    raise

        if conn is None:
            # Pool cheio - espera e tenta novamente
            import time
            for _ in range(100):  # até 5 segundos
                time.sleep(0.05)
                with self._pool_lock:
                    if self._connections:
                        conn = self._connections.pop()
                        self._active_count += 1
                        break
            if conn is None:
                raise sqlite3.OperationalError(
                    "Pool de conexões SQLite esgotado — todas as "
                    f"{self.max_connections} conexões estão em uso"
                )

        try:
            yield conn
        finally:
            self._return_connection(conn)

    def _return_connection(self, conn: sqlite3.Connection):
        """Devolve uma conexão ao pool"""
        try:
            with self._pool_lock:
                self._active_count -= 1
                if len(self._connections) < self.max_connections:
                    self._connections.append(conn)
                else:
                    conn.close()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    def close_all(self):
        """Fecha todas as conexões do pool"""
        with self._pool_lock:
            for conn in self._connections:
                try:
                    conn.close()
                except Exception:
                    pass
            self._connections.clear()
            self._active_count = 0

    @property
    def stats(self) -> dict:
        """Retorna estatísticas do pool"""
        with self._pool_lock:
            return {
                "pool_size": len(self._connections),
                "active": self._active_count,
                "max": self.max_connections,
            }


def get_db_pool(db_path: str = None) -> SQLiteConnectionPool:
    """Convenience function para obter o pool"""
    if db_path is None:
        import config
        db_path = config.DB_PATH
    return SQLiteConnectionPool.get_instance(db_path)
