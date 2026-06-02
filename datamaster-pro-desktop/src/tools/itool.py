"""
ITool - Interface base para todas as ferramentas
Define contrato comum para execução, metadados e registro automático.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, Callable


class ITool(ABC):
    """Interface que toda ferramenta deve implementar."""

    # Metadados da ferramenta (subclasses devem sobrescrever)
    TOOL_KEY: str = ""
    TOOL_NAME: str = ""
    TOOL_PAGE_MODULE: str = ""

    @abstractmethod
    def execute(self, params: dict) -> dict:
        """Executa a ferramenta com os parâmetros fornecidos.
        
        Returns:
            dict com pelo menos 'success' (bool) e opcionalmente
            'output_path', 'rows_processed', 'hours_saved'.
        """
        ...

    def get_progress(self) -> tuple[int, str]:
        """Retorna (percentual, mensagem) do progresso atual.
        Padrão: sem progresso reportado.
        """
        return 0, ""

    def cancel(self):
        """Solicita cancelamento da execução. Padrão: não-op."""
        pass


# ── Registro automático ──────────────────────────────────────────────────────

_TOOL_REGISTRY: Dict[str, type] = {}
_TOOL_PAGE_MAP: Dict[str, str] = {}


def register_tool(tool_key: str, tool_name: str = "", page_module: str = ""):
    """Decorator que registra uma ferramenta automaticamente.
    
    Uso:
        @register_tool("minerador", "Minerador de Preços",
                        "src.gui.pages.tools.minerador_page")
        class Minerador(ITool):
            ...
    """
    def decorator(cls):
        _TOOL_REGISTRY[tool_key] = cls
        if page_module:
            _TOOL_PAGE_MAP[tool_key] = page_module
        # Injeta metadados na classe
        cls.TOOL_KEY = tool_key
        cls.TOOL_NAME = tool_name or tool_key
        cls.TOOL_PAGE_MODULE = page_module
        return cls
    return decorator


def get_all_tools() -> Dict[str, type]:
    """Retorna todas as ferramentas registradas."""
    return dict(_TOOL_REGISTRY)


def get_tool_page_map() -> Dict[str, str]:
    """Retorna mapeamento tool_key -> page_module."""
    return dict(_TOOL_PAGE_MAP)


def get_tool_class(tool_key: str) -> Optional[type]:
    """Retorna a classe de uma ferramenta pelo key."""
    return _TOOL_REGISTRY.get(tool_key)


def register_all_tools(task_manager):
    """Registra todas as ferramentas no task_manager (compatibilidade)."""
    for tool_name, tool_class in _TOOL_REGISTRY.items():
        task_manager.register_tool(tool_name, tool_class)
