"""
ITool Adapter for Categorizador
"""
from src.tools.itool import ITool, register_tool
from src.tools.categorizador.categorizador_v2 import Categorizador
from typing import Dict, Any, Optional
import logging

log = logging.getLogger(__name__)


@register_tool("categorizador", "Categorizador", "src.gui.pages.tools.categorizador_page")
class CategorizadorTool(ITool):
    TOOL_KEY = "categorizador"
    TOOL_NAME = "Categorizador"
    TOOL_PAGE_MODULE = "src.gui.pages.tools.categorizador_page"

    def __init__(self, progress_callback: Optional[callable] = None, log_callback: Optional[callable] = None):
        self._engine = Categorizador()
        self._progress_callback = progress_callback
        self._log_callback = log_callback
        self._current_progress = 0
        self._cancelled = False

    def _log(self, msg: str):
        log.info(msg)
        if self._log_callback:
            self._log_callback(msg)

    def _progress(self, pct: int, msg: str = ""):
        if self._progress_callback:
            self._progress_callback(pct, msg)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o categorizador com os parâmetros fornecidos.
        
        params:
            input_path: str - arquivo de entrada (xlsx, xls, csv)
            output_path: str - caminho do arquivo de saída
            description_column: str = "descricao" - coluna com texto a categorizar
            category_column: str = "categoria" - coluna de saída
            visual_theme: str = "classic_blue" - tema visual do Excel
        """
        try:
            self._progress(0, "Iniciando categorização...")
            
            result = self._engine.categorize(
                input_path=params.get("input_path", ""),
                output_path=params.get("output_path", ""),
                description_column=params.get("description_column", "descricao"),
                category_column=params.get("category_column", "categoria"),
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