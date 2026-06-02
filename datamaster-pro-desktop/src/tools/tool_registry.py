"""
Tool Registry - Registro de todas as ferramentas disponíveis
Usado pelo TaskManager para executar tarefas em background.

Suporta três modos de registro:
1. @plugin decorator (novo) - auto-registra com metadados
2. @register_tool decorator (legado) - auto-registra ao definir a classe
3. Dict manual TOOL_REGISTRY (legado) - mantido para compatibilidade
"""
import logging

log = logging.getLogger(__name__)

from src.tools.itool import (
    ITool, register_tool, get_all_tools, get_tool_page_map,
    get_tool_class, _TOOL_REGISTRY, _TOOL_PAGE_MAP,
)
from src.domain.plugin_registry import PluginRegistry

# ── Ferramentas legadas (serão migradas para @register_tool gradualmente) ────

_LEGACY_IMPORTS = {
    "minerador": ("src.tools.minerador.minerador_v2", "Minerador"),
    "comissoes": ("src.tools.comissoes.comissoes", "Comissoes"),
    "conciliador": ("src.tools.conciliador.conciliador_v2", "Conciliador"),
    "categorizador": ("src.tools.categorizador.categorizador_v2", "Categorizador"),
    "orcamentos": ("src.tools.orcamentos.orcamentos", "Orcamentos"),
    "consolidador": ("src.tools.consolidador.consolidador_v2", "Consolidador"),
    "calculadora_lucratividade": ("src.tools.calculadora_lucratividade.calculadora_lucratividade_v2", "CalculadoraLucratividade"),
    "analista_tendencias": ("src.tools.analista_tendencias.analista_tendencias_v2", "AnalistaTendencias"),
    "data_sanitizer": ("src.tools.data_sanitizer.data_sanitizer_v2", "DataSanitizer"),
    "extrator_reviews": ("src.tools.extrator_reviews.extrator_reviews_v2", "ExtratorReviews"),
    "validador_links": ("src.tools.validador_links.validador_links_v2", "ValidadorLinks"),
    "conversor_ocr": ("src.tools.conversor_ocr.conversor_ocr_v2", "ConversorOCR"),
    "gerador_laudos": ("src.tools.gerador_laudos.gerador_laudos_v2", "GeradorLaudos"),
    "precificador_canal": ("src.tools.precificador_canal.precificador_canal_v1", "PrecificadorCanal"),
    "extrator_nfe": ("src.tools.extrator_nfe.extrator_nfe_v1", "ExtratorNFe"),
    "classificador_ncm": ("src.tools.classificador_ncm.classificador_ncm_v1", "ClassificadorNCM"),
}

# Mapeamento tool_key -> page_module (legado)
LEGACY_PAGE_MODULES = {
    "consolidador": "src.gui.pages.tools.consolidador_page",
    "categorizador": "src.gui.pages.tools.categorizador_page",
    "orcamentos": "src.gui.pages.tools.orcamentos_page",
    "minerador": "src.gui.pages.tools.minerador_page",
    "conciliador": "src.gui.pages.tools.conciliador_page",
    "validador_links": "src.gui.pages.tools.validador_links_page",
    "extrator_reviews": "src.gui.pages.tools.extrator_reviews_page",
    "calculadora_lucratividade": "src.gui.pages.tools.calculadora_lucratividade_page",
    "analista_tendencias": "src.gui.pages.tools.analista_tendencias_page",
    "data_sanitizer": "src.gui.pages.tools.data_sanitizer_page",
    "conversor_ocr": "src.gui.pages.tools.conversor_ocr_page",
    "gerador_laudos": "src.gui.pages.tools.gerador_laudos_page",
    "comissoes": "src.gui.pages.tools.comissoes_page",
    "classificador_ncm": "src.gui.pages.tools.classificador_ncm_page",
    "precificador_canal": "src.gui.pages.tools.precificador_canal_page",
}


def _ensure_legacy_registered():
    """Registra ferramentas legadas que ainda usam import manual."""
    import importlib

    # 1. Registra do PluginRegistry (auto-discovery)
    plugin_reg = PluginRegistry.get_instance()
    plugin_reg.discover()
    for key in plugin_reg.get_all_keys():
        if key not in _TOOL_REGISTRY:
            cls = plugin_reg.get_tool_class(key)
            if cls:
                _TOOL_REGISTRY[key] = cls
                page = plugin_reg.get_page_module(key)
                if page:
                    _TOOL_PAGE_MAP[key] = page

    # 2. Registra ferramentas legadas manuais
    for tool_key, (module_path, class_name) in _LEGACY_IMPORTS.items():
        if tool_key in _TOOL_REGISTRY:
            continue
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            _TOOL_REGISTRY[tool_key] = cls
            if tool_key in LEGACY_PAGE_MODULES:
                _TOOL_PAGE_MAP[tool_key] = LEGACY_PAGE_MODULES[tool_key]
        except Exception as e:
            log.error("Erro ao registrar ferramenta legada %s: %s", tool_key, e)


_ensure_legacy_registered()

# ── API pública (compatível com código existente) ────────────────────────────

TOOL_REGISTRY = _TOOL_REGISTRY

TOOL_PAGE_MODULES = dict(_TOOL_PAGE_MAP)


def register_all_tools(task_manager):
    """Registra todas as ferramentas no task_manager"""
    for tool_name, tool_class in _TOOL_REGISTRY.items():
        task_manager.register_tool(tool_name, tool_class)
