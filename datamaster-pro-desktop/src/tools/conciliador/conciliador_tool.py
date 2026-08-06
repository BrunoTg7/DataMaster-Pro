"""
ITool Adapter for Conciliador
"""
from src.tools.itool import ITool, register_tool
from src.tools.conciliador.conciliador_v2 import Conciliador
from typing import Dict, Any, Optional
import logging

log = logging.getLogger(__name__)


@register_tool("conciliador", "Conciliador", "src.gui.pages.tools.conciliador_page")
class ConciliadorTool(ITool):
    TOOL_KEY = "conciliador"
    TOOL_NAME = "Conciliador"
    TOOL_PAGE_MODULE = "src.gui.pages.tools.conciliador_page"

    def __init__(self, progress_callback: Optional[callable] = None, log_callback: Optional[callable] = None):
        self._engine = Conciliador(log_callback=log_callback, progress_callback=progress_callback)
        self._progress_callback = progress_callback
        self._log_callback = log_callback
        self._current_progress = 0
        self._cancelled = False

    def _log(self, msg: str):
        if self._log_callback:
            self._log_callback(msg)

    def _progress(self, pct: int, msg: str = ""):
        if self._progress_callback:
            self._progress_callback(pct, msg)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o conciliador com os parâmetros fornecidos.
        
        params (modo classic):
            mode: str = "classic"
            extract_file: str - arquivo de extrato bancário
            sales_file: str - arquivo de planilha de vendas
            output_path: str - arquivo de saída
            tolerance: float = 0.01
            date_tolerance_days: int = 2
            fuzzy_threshold: int = 75
            visual_theme: str = "classic_blue"
        
        params (modo nfe):
            mode: str = "nfe"
            xml_folder: str - pasta com XMLs de NF-e
            bank_file: str - arquivo de extrato bancário
            output_path: str
            tolerance: float = 0.05
            date_tolerance_days: int = 5
            fuzzy_threshold: int = 60
            visual_theme: str = "classic_blue"
        
        params (modo nfe_vendas):
            mode: str = "nfe_vendas"
            xml_folder: str - pasta com XMLs de NF-e
            sales_file: str - planilha de vendas
            output_path: str
            tolerance: float = 0.01
            chave: str = "auto"
            visual_theme: str = "classic_blue"
        """
        try:
            self._progress(0, "Iniciando conciliação...")
            
            mode = params.get("mode", "classic")
            
            if mode == "nfe":
                result = self._engine.reconcile_nfe(
                    xml_folder=params.get("xml_folder", ""),
                    bank_file=params.get("bank_file", ""),
                    output_path=params.get("output_path", ""),
                    tolerance=params.get("tolerance", 0.05),
                    date_tolerance_days=params.get("date_tolerance_days", 5),
                    fuzzy_threshold=params.get("fuzzy_threshold", 60),
                    visual_theme=params.get("visual_theme", "classic_blue"),
                )
            elif mode == "nfe_vendas":
                result = self._engine.reconcile_nfe_vendas(
                    xml_folder=params.get("xml_folder", ""),
                    sales_file=params.get("sales_file", ""),
                    output_path=params.get("output_path", ""),
                    tolerance=params.get("tolerance", 0.01),
                    chave=params.get("chave", "auto"),
                    visual_theme=params.get("visual_theme", "classic_blue"),
                )
            else:  # classic
                result = self._engine.reconcile_classic(
                    extract_file=params.get("extract_file", ""),
                    sales_file=params.get("sales_file", ""),
                    output_path=params.get("output_path", ""),
                    tolerance=params.get("tolerance", 0.01),
                    date_tolerance_days=params.get("date_tolerance_days", 2),
                    fuzzy_threshold=params.get("fuzzy_threshold", 75),
                    visual_theme=params.get("visual_theme", "classic_blue"),
                )
            
            if result.get("success"):
                self._progress(100, "Concluído")
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_progress(self) -> tuple[int, str]:
        return self._current_progress, ""

    def cancel(self):
        self._cancelled = True