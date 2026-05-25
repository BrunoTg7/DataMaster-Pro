"""
Tool Registry - Registro de todas as ferramentas disponíveis
Usado pelo TaskManager para executar tarefas em background
"""

from src.tools.minerador.minerador_v2 import Minerador
from src.tools.comissoes.comissoes import Comissoes
from src.tools.conciliador.conciliador_v2 import Conciliador
from src.tools.categorizador.categorizador_v2 import Categorizador
from src.tools.orcamentos.orcamentos import Orcamentos
from src.tools.consolidador.consolidador_v2 import Consolidador
from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
from src.tools.analista_tendencias.analista_tendencias_v2 import AnalistaTendencias
from src.tools.data_sanitizer.data_sanitizer_v2 import DataSanitizer
from src.tools.extrator_reviews.extrator_reviews_v2 import ExtratorReviews
from src.tools.validador_links.validador_links_v2 import ValidadorLinks
from src.tools.conversor_ocr.conversor_ocr_v2 import ConversorOCR
from src.tools.gerador_laudos.gerador_laudos_v2 import GeradorLaudos


TOOL_REGISTRY = {
    "minerador": Minerador,
    "comissoes": Comissoes,
    "conciliador": Conciliador,
    "categorizador": Categorizador,
    "orcamentos": Orcamentos,
    "consolidador": Consolidador,
    "calculadora_lucratividade": CalculadoraLucratividade,
    "analista_tendencias": AnalistaTendencias,
    "data_sanitizer": DataSanitizer,
    "extrator_reviews": ExtratorReviews,
    "validador_links": ValidadorLinks,
    "conversor_ocr": ConversorOCR,
    "gerador_laudos": GeradorLaudos,
}


def register_all_tools(task_manager):
    """Registra todas as ferramentas no task_manager"""
    for tool_name, tool_class in TOOL_REGISTRY.items():
        task_manager.register_tool(tool_name, tool_class)