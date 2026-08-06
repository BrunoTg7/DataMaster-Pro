"""
Audit Logger - Registra eventos de segurança e compliance.
Escreve em logs/audit.log com formato estruturado.
"""
import logging
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_audit_logger: Optional[logging.Logger] = None


def get_audit_logger() -> logging.Logger:
    global _audit_logger
    if _audit_logger is not None:
        return _audit_logger

    _audit_logger = logging.getLogger("audit")
    _audit_logger.setLevel(logging.INFO)
    _audit_logger.propagate = False

    if not _audit_logger.handlers:
        from src.core.session_context import SessionFilter
        _audit_logger.addFilter(SessionFilter())

    return _audit_logger


def audit(event: str, *, user_id: str = None, details: dict = None, level: str = "info"):
    """Registra um evento de auditoria.

    Args:
        event: Tipo do evento (login, logout, export, plan_change, etc.)
        user_id: ID do usuário (auto-detectado do contexto se None)
        details: Dados adicionais do evento
        level: Nível do log (info, warning, error)
    """
    from src.core.session_context import get_user_id, get_session_id

    log = get_audit_logger()

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user_id": user_id or get_user_id() or "anonymous",
        "session_id": get_session_id(),
    }
    if details:
        record["details"] = details

    msg = json.dumps(record, ensure_ascii=False, default=str)

    log_func = getattr(log, level, log.info)
    log_func(msg)


def audit_login(user_id: str, success: bool, method: str = "password", error: str = None):
    details = {"method": method, "success": success}
    if error:
        details["error"] = error
    audit("login", user_id=user_id, details=details, level="info" if success else "warning")


def audit_logout(user_id: str):
    audit("logout", user_id=user_id)


def audit_export(user_id: str, tool: str, file_count: int, rows: int):
    audit("export", user_id=user_id, details={"tool": tool, "files": file_count, "rows": rows})


def audit_plan_change(user_id: str, old_plan: str, new_plan: str, reason: str = None):
    details = {"old_plan": old_plan, "new_plan": new_plan}
    if reason:
        details["reason"] = reason
    audit("plan_change", user_id=user_id, details=details, level="warning")


def audit_sync(user_id: str, direction: str, records: int, success: bool):
    audit("sync", user_id=user_id, details={"dir": direction, "records": records, "success": success})


def audit_settings_change(user_id: str, setting: str, old_value, new_value):
    audit("settings_change", user_id=user_id, details={"setting": setting, "old": old_value, "new": new_value})


def audit_lgpd_export(user_id: str, record_count: int, export_format: str):
    audit("lgpd_export", user_id=user_id, details={"records": record_count, "format": export_format})


def audit_lgpd_delete_request(user_id: str, grace_days: int = 30):
    audit("lgpd_delete_request", user_id=user_id, details={"grace_days": grace_days}, level="warning")


def audit_lgpd_delete_confirmed(user_id: str):
    audit("lgpd_delete_confirmed", user_id=user_id, level="warning")


def audit_lgpd_consent(user_id: str, consented: bool, method: str = "checkbox"):
    audit("lgpd_consent", user_id=user_id, details={"consented": consented, "method": method})
