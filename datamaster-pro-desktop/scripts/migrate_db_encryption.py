"""
Migração de Criptografia - Criptografa dados existentes em texto plano.
Execute uma única vez. Idempotente: dados já criptografados são ignorados.
"""
import os
import sys
import sqlite3
import logging

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.storage.db_encryption import DBEncryption, needs_encryption, ENC_PREFIX

log = logging.getLogger(__name__)


def _is_encrypted(data: str) -> bool:
    """Verifica se dados já estão criptografados."""
    return bool(data) and data.startswith(ENC_PREFIX)


def migrate_users(conn: sqlite3.Connection, enc: DBEncryption) -> int:
    """Criptografa colunas sensíveis da tabela users."""
    cursor = conn.cursor()
    rows = cursor.execute("SELECT rowid, email, plan, expires_at, session_token_encrypted, "
                          "refresh_token_encrypted, data_expiracao FROM users").fetchall()
    migrated = 0
    for rowid, email, plan, expires, session, refresh, data_exp in rows:
        updates = []
        values = []
        if email and not _is_encrypted(email):
            updates.append("email = ?")
            values.append(enc.encrypt(email))
        if plan and not _is_encrypted(plan):
            updates.append("plan = ?")
            values.append(enc.encrypt(plan))
        if expires and not _is_encrypted(expires):
            updates.append("expires_at = ?")
            values.append(enc.encrypt(expires))
        if session and not _is_encrypted(session):
            updates.append("session_token_encrypted = ?")
            values.append(enc.encrypt(session))
        if refresh and not _is_encrypted(refresh):
            updates.append("refresh_token_encrypted = ?")
            values.append(enc.encrypt(refresh))
        if data_exp and not _is_encrypted(data_exp):
            updates.append("data_expiracao = ?")
            values.append(enc.encrypt(data_exp))
        if updates:
            values.append(rowid)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE rowid = ?", values)
            migrated += 1
    return migrated


def migrate_tasks(conn: sqlite3.Connection, enc: DBEncryption) -> int:
    """Criptografa colunas sensíveis da tabela tasks."""
    cursor = conn.cursor()
    rows = cursor.execute("SELECT rowid, input_params, output_path, log_text, "
                          "error_message, progress_message FROM tasks").fetchall()
    migrated = 0
    for rowid, input_p, output, log_t, error, progress in rows:
        updates = []
        values = []
        if input_p and not _is_encrypted(input_p):
            updates.append("input_params = ?")
            values.append(enc.encrypt(input_p))
        if output and not _is_encrypted(output):
            updates.append("output_path = ?")
            values.append(enc.encrypt(output))
        if log_t and not _is_encrypted(log_t):
            updates.append("log_text = ?")
            values.append(enc.encrypt(log_t))
        if error and not _is_encrypted(error):
            updates.append("error_message = ?")
            values.append(enc.encrypt(error))
        if progress and not _is_encrypted(progress):
            updates.append("progress_message = ?")
            values.append(enc.encrypt(progress))
        if updates:
            values.append(rowid)
            cursor.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE rowid = ?", values)
            migrated += 1
    return migrated


def migrate_executions(conn: sqlite3.Connection, enc: DBEncryption) -> int:
    """Criptografa colunas sensíveis da tabela executions."""
    cursor = conn.cursor()
    rows = cursor.execute("SELECT rowid, input_files, output_file FROM executions").fetchall()
    migrated = 0
    for rowid, input_f, output_f in rows:
        updates = []
        values = []
        if input_f and not _is_encrypted(input_f):
            updates.append("input_files = ?")
            values.append(enc.encrypt(input_f))
        if output_f and not _is_encrypted(output_f):
            updates.append("output_file = ?")
            values.append(enc.encrypt(output_f))
        if updates:
            values.append(rowid)
            cursor.execute(f"UPDATE executions SET {', '.join(updates)} WHERE rowid = ?", values)
            migrated += 1
    return migrated


def migrate_execution_logs(conn: sqlite3.Connection, enc: DBEncryption) -> int:
    """Criptografa colunas sensíveis da tabela execution_logs_local."""
    cursor = conn.cursor()

    # Verificar colunas existentes (schema pode variar)
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(execution_logs_local)").fetchall()}
    migrated = 0

    # Criptografar error_message se existir
    if "error_message" in cols:
        rows = cursor.execute("SELECT rowid, error_message FROM execution_logs_local").fetchall()
        for rowid, error in rows:
            if error and not _is_encrypted(error):
                cursor.execute("UPDATE execution_logs_local SET error_message = ? WHERE rowid = ?",
                               (enc.encrypt(error), rowid))
                migrated += 1

    # Criptografar details_json se existir (schema antigo)
    if "details_json" in cols:
        rows = cursor.execute("SELECT rowid, details_json FROM execution_logs_local").fetchall()
        for rowid, details in rows:
            if details and not _is_encrypted(details):
                cursor.execute("UPDATE execution_logs_local SET details_json = ? WHERE rowid = ?",
                               (enc.encrypt(details), rowid))
                migrated += 1

    return migrated


def migrate_scheduled_tasks(conn: sqlite3.Connection, enc: DBEncryption) -> int:
    """Criptografa colunas sensíveis da tabela scheduled_tasks_local."""
    cursor = conn.cursor()
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(scheduled_tasks_local)").fetchall()}
    migrated = 0

    if "task_name" in cols:
        rows = cursor.execute("SELECT rowid, task_name FROM scheduled_tasks_local").fetchall()
        for rowid, name in rows:
            if name and not _is_encrypted(name):
                cursor.execute("UPDATE scheduled_tasks_local SET task_name = ? WHERE rowid = ?",
                               (enc.encrypt(name), rowid))
                migrated += 1

    if "input_files" in cols:
        rows = cursor.execute("SELECT rowid, input_files FROM scheduled_tasks_local").fetchall()
        for rowid, files in rows:
            if files and not _is_encrypted(files):
                cursor.execute("UPDATE scheduled_tasks_local SET input_files = ? WHERE rowid = ?",
                               (enc.encrypt(files), rowid))
                migrated += 1

    if "config" in cols:
        rows = cursor.execute("SELECT rowid, config FROM scheduled_tasks_local").fetchall()
        for rowid, config in rows:
            if config and not _is_encrypted(config):
                cursor.execute("UPDATE scheduled_tasks_local SET config = ? WHERE rowid = ?",
                               (enc.encrypt(config), rowid))
                migrated += 1

    if "last_error" in cols:
        rows = cursor.execute("SELECT rowid, last_error FROM scheduled_tasks_local").fetchall()
        for rowid, error in rows:
            if error and not _is_encrypted(error):
                cursor.execute("UPDATE scheduled_tasks_local SET last_error = ? WHERE rowid = ?",
                               (enc.encrypt(error), rowid))
                migrated += 1

    return migrated


def migrate_tool_configurations(conn: sqlite3.Connection, enc: DBEncryption) -> int:
    """Criptografa colunas sensíveis da tabela tool_configurations_local."""
    cursor = conn.cursor()
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(tool_configurations_local)").fetchall()}
    migrated = 0

    if "config_data" in cols:
        rows = cursor.execute("SELECT rowid, config_data FROM tool_configurations_local").fetchall()
        for rowid, config in rows:
            if config and not _is_encrypted(config):
                cursor.execute("UPDATE tool_configurations_local SET config_data = ? WHERE rowid = ?",
                               (enc.encrypt(config), rowid))
                migrated += 1

    if "config_json" in cols:
        rows = cursor.execute("SELECT rowid, config_json FROM tool_configurations_local").fetchall()
        for rowid, config in rows:
            if config and not _is_encrypted(config):
                cursor.execute("UPDATE tool_configurations_local SET config_json = ? WHERE rowid = ?",
                               (enc.encrypt(config), rowid))
                migrated += 1

    if "description" in cols:
        rows = cursor.execute("SELECT rowid, description FROM tool_configurations_local").fetchall()
        for rowid, desc in rows:
            if desc and not _is_encrypted(desc):
                cursor.execute("UPDATE tool_configurations_local SET description = ? WHERE rowid = ?",
                               (enc.encrypt(desc), rowid))
                migrated += 1

    return migrated


def migrate_settings(conn: sqlite3.Connection, enc: DBEncryption) -> int:
    """Criptografa valores sensíveis da tabela settings."""
    cursor = conn.cursor()
    rows = cursor.execute("SELECT rowid, key, value FROM settings").fetchall()
    migrated = 0
    for rowid, key, value in rows:
        # Criptografar valores de deletion e consent, mas não temas
        if key.startswith("deletion_scheduled_") or key.startswith("lgpd_consent_"):
            if value and not _is_encrypted(value):
                cursor.execute("UPDATE settings SET value = ? WHERE rowid = ?",
                               (enc.encrypt(value), rowid))
                migrated += 1
    return migrated


def run_migration(db_path: str):
    """Executa migração completa de criptografia."""
    # Usar a mesma derivação de chave do StorageManager
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config
    from src.core.security.security_manager import SecurityManager

    # Replicar _derive_encryption_key() do StorageManager
    env_key = config.ENCRYPTION_KEY
    if env_key and env_key != "your-secret-key-32-chars-here!" and len(env_key) >= 16:
        base_key = env_key
    else:
        key_file = os.path.join(os.path.dirname(db_path), ".encryption_key")
        if os.path.exists(key_file):
            with open(key_file, "r") as f:
                base_key = f.read().strip()
            if not base_key or len(base_key) < 16:
                base_key = os.urandom(32).hex()
                with open(key_file, "w") as f:
                    f.write(base_key)
        else:
            base_key = os.urandom(32).hex()
            try:
                with open(key_file, "w") as f:
                    f.write(base_key)
            except OSError:
                pass

    hwid = SecurityManager.get_hwid()
    if not hwid or len(hwid) < 16:
        hw_key = base_key
    else:
        hw_key = f"{base_key}-{hwid[:16]}"

    # Usar hw_key diretamente como password (sem HWID adicional)
    enc = DBEncryption(password=hw_key, hwid="")

    if not os.path.exists(db_path):
        log.info("Banco de dados não encontrado: %s — migração ignorada", db_path)
        return

    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")

    total = 0
    try:
        total += migrate_users(conn, enc)
        total += migrate_tasks(conn, enc)
        total += migrate_executions(conn, enc)
        total += migrate_execution_logs(conn, enc)
        total += migrate_scheduled_tasks(conn, enc)
        total += migrate_tool_configurations(conn, enc)
        total += migrate_settings(conn, enc)
        conn.commit()
    except Exception as e:
        conn.rollback()
        log.error("Erro na migração de criptografia: %s", e)
        raise
    finally:
        conn.close()

    if total > 0:
        log.info("Migração de criptografia concluída: %d registros criptografados", total)
    else:
        log.info("Nenhum dado novo para criptografar")


if __name__ == "__main__":
    import config
    run_migration(config.DB_PATH)
