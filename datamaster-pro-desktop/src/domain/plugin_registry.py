"""
Plugin System - Auto-discovery e registro de ferramentas
Substitui o registry manual. Novas ferramentas se auto-registram.
"""
import importlib
import logging
import os
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type
from src.domain.entities import ToolMetadata

log = logging.getLogger(__name__)


class PluginRegistry:
    """Registry central de plugins/ferramentas com auto-discovery."""

    _instance: Optional["PluginRegistry"] = None

    def __init__(self):
        self._plugins: Dict[str, dict] = {}
        self._page_map: Dict[str, str] = {}
        self._discovered = False

    @classmethod
    def get_instance(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(
        self,
        key: str,
        tool_class: Type,
        metadata: ToolMetadata = None,
        page_module: str = "",
    ):
        """Registra uma ferramenta manualmente."""
        self._plugins[key] = {
            "class": tool_class,
            "metadata": metadata or ToolMetadata(key=key, name=key),
            "page_module": page_module,
        }
        if page_module:
            self._page_map[key] = page_module
        log.debug("Plugin registrado: %s", key)

    def discover(self, tools_dir: str = None):
        """Auto-descobre ferramentas no diretório tools/."""
        if self._discovered:
            return

        if tools_dir is None:
            tools_dir = str(Path(__file__).parent.parent.parent / "src" / "tools")

        # Percorre subdiretórios de tools/
        for _, tool_name, _ in pkgutil.iter_modules([tools_dir]):
            tool_path = os.path.join(tools_dir, tool_name)
            if not os.path.isdir(tool_path):
                continue

            # Procura por módulos Python no diretório da ferramenta
            for _, module_name, _ in pkgutil.iter_modules([tool_path]):
                if module_name.startswith("_"):
                    continue

                try:
                    module_path = f"src.tools.{tool_name}.{module_name}"
                    module = importlib.import_module(module_path)

                    # Procura classes que tenham TOOL_KEY ou decorem com @register_tool
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if not isinstance(attr, type):
                            continue

                        # Auto-registro via atributo TOOL_KEY
                        tool_key = getattr(attr, "TOOL_KEY", None)
                        if tool_key and tool_key not in self._plugins:
                            self.register(tool_key, attr, page_module="")
                            log.info("Auto-descoberto: %s (from %s)", tool_key, module_path)

                except Exception as e:
                    log.debug("Erro ao importar %s: %s", module_name, e)

        self._discovered = True
        log.info("Plugin discovery completo: %d plugins", len(self._plugins))

    def get_tool_class(self, key: str) -> Optional[Type]:
        """Retorna a classe de uma ferramenta."""
        plugin = self._plugins.get(key)
        return plugin["class"] if plugin else None

    def get_metadata(self, key: str) -> Optional[ToolMetadata]:
        """Retorna metadados de uma ferramenta."""
        plugin = self._plugins.get(key)
        return plugin["metadata"] if plugin else None

    def get_page_module(self, key: str) -> Optional[str]:
        """Retorna o módulo da página GUI de uma ferramenta."""
        return self._page_map.get(key)

    def get_all_plugins(self) -> Dict[str, dict]:
        """Retorna todos os plugins registrados."""
        return dict(self._plugins)

    def get_all_keys(self) -> List[str]:
        """Retorna todas as chaves de ferramentas."""
        return list(self._plugins.keys())

    def get_all_page_modules(self) -> Dict[str, str]:
        """Retorna mapeamento tool_key -> page_module."""
        return dict(self._page_map)

    def is_registered(self, key: str) -> bool:
        """Verifica se uma ferramenta está registrada."""
        return key in self._plugins

    def unregister(self, key: str):
        """Remove uma ferramenta do registry."""
        self._plugins.pop(key, None)
        self._page_map.pop(key, None)

    def register_page_module(self, tool_key: str, page_module: str):
        """Registra módulo de página para uma ferramenta."""
        self._page_map[tool_key] = page_module
        if tool_key in self._plugins:
            self._plugins[tool_key]["page_module"] = page_module

    def register_all_to_executor(self, executor):
        """Registra todas as ferramentas no TaskExecutor (compatibilidade)."""
        for key, plugin in self._plugins.items():
            executor.register_tool(key, plugin["class"])


# ── Decorator para auto-registro ─────────────────────────────────────────────

def plugin(
    key: str,
    name: str = "",
    version: str = "1.0.0",
    description: str = "",
    page_module: str = "",
    min_plan: str = "gratis",
):
    """Decorator para auto-registrar uma ferramenta como plugin.

    Uso:
        @plugin("minerador", "Minerador de Preços", page_module="src.gui.pages.tools.minerador_page")
        class Minerador:
            ...
    """
    def decorator(cls):
        from src.domain.entities import PlanType
        metadata = ToolMetadata(
            key=key,
            name=name or key,
            version=version,
            description=description,
            page_module=page_module,
            min_plan=PlanType(min_plan),
        )
        cls.TOOL_KEY = key
        cls.TOOL_METADATA = metadata
        PluginRegistry.get_instance().register(key, cls, metadata, page_module)
        return cls
    return decorator
