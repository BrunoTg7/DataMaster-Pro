"""
Application Services - Camada de serviço entre GUI e Core
Encapsula lógica de negócio para desacoplar apresentação de domínio.
"""
from src.core.services.tool_service import ToolService
from src.core.services.user_service import UserService

_tool_service_instance = None
_user_service_instance = None


def get_tool_service() -> ToolService:
    global _tool_service_instance
    if _tool_service_instance is None:
        _tool_service_instance = ToolService()
    return _tool_service_instance


def get_user_service() -> UserService:
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance
