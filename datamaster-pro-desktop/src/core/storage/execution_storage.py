"""
Execution Storage - Gerencia histórico de execuções e logs.
"""
import sqlite3
import json
import logging
from typing import List, Dict

log = logging.getLogger(__name__)


class ExecutionStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def save_execution(self, user_id: str, tool_name: str, input_files: List[str],
                       output_file: str, rows_processed: int = 0, hours_saved: float = 0):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO executions (user_id, tool_name, input_files, output_file,
                status, rows_processed, hours_saved)
            VALUES (?, ?, ?, ?, 'completed', ?, ?)
        """, (user_id, tool_name, json.dumps(input_files), output_file, rows_processed, hours_saved))
        conn.commit()
        conn.close()

    def replace_user_executions(self, user_id: str, records: List[Dict]):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            conn.execute("BEGIN")
            cursor.execute("DELETE FROM executions WHERE user_id = ?", (user_id,))
            insert_data = []
            for record in records:
                insert_data.append((
                    user_id,
                    record.get("ferramenta") or record.get("tool_name", ""),
                    json.dumps(record.get("input_files", [])),
                    record.get("resultado_arquivo") or record.get("output_file", ""),
                    record.get("status", "completed"),
                    int(record.get("linhas_processadas") or record.get("rows_processed", 0)),
                    float(record.get("tempo_execucao_ms", 0)),
                    float(record.get("tempo_economizado_minutos", 0)),
                    record.get("created_at", ""),
                ))
            cursor.executemany("""
                INSERT INTO executions (user_id, tool_name, input_files, output_file,
                    status, rows_processed, hours_saved, tempo_execucao_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, insert_data)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def get_executions(self, user_id: str, limit: int = 100) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tool_name, input_files, output_file, status, created_at,
                rows_processed, hours_saved
            FROM executions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": row[0], "tool_name": row[1], "input_files": row[2],
                "output_file": row[3], "status": row[4], "created_at": row[5],
                "rows_processed": row[6], "hours_saved": row[7]
            }
            for row in rows
        ]

    def cleanup_executions_duplicates(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM executions WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM executions
                GROUP BY user_id, tool_name, created_at
            )
        """)
        removed = cursor.rowcount
        conn.commit()
        conn.close()
        if removed > 0:
            log.info("Removidas %d execuções duplicadas", removed)
        return removed

    def save_execution_log(self, user_id: str, tool_name: str, status: str,
                           details: dict = None):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO execution_logs_local (user_id, tool_name, status, details_json, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, tool_name, status, json.dumps(details or {})))
        conn.commit()
        conn.close()

    def get_execution_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tool_name, status, details_json, created_at
            FROM execution_logs_local WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {"id": r[0], "tool_name": r[1], "status": r[2], "details": json.loads(r[3] or "{}"), "created_at": r[4]}
            for r in rows
        ]
