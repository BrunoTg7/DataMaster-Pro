"""Session context for log correlation across the application."""
import logging
import uuid
from contextvars import ContextVar

_session_id = ContextVar("session_id", default="")
_user_id = ContextVar("user_id", default="")


def set_session_id(sid=None):
    if sid is None:
        sid = uuid.uuid4().hex[:12]
    _session_id.set(sid)
    return sid


def get_session_id():
    return _session_id.get("")


def set_user_id(uid=None):
    _user_id.set(uid or "")


def get_user_id():
    return _user_id.get("")


class SessionFilter(logging.Filter):
    def filter(self, record):
        record.session_id = get_session_id()
        record.user_id = get_user_id()
        return True
