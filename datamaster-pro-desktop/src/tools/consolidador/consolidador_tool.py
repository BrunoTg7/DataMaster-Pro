"""
ITool Adapter for Consolidador
"""
from src.tools.itool import ITool, register_tool
from src.tools.consolidador.consolidador_v2 import Consolidador
from typing import Dict, Any, Optional
import logging

log = logging.getLogger(__name__)


@register_tool("consolidador", "Consolidador", "src.gui.pages.tools.consolidador_page")
class ConsolidadorTool(ITool):
    TOOL_KEY = "consolidador"
    TOOL_NAME = "Consolidador"
    TOOL_PAGE_MODULE = "src.gui.pages.tools.consolidador_page"

    def __init__(self, progress_callback: Optional[callable] = None, log_callback: Optional[callable] = None):
        self._engine = Consolidador()
        self._progress_callback = progress_callback
        self._log_callback = log_callback
        self._current_progress = 0
        self._cancelled = False

    def _log(self, msg: str):
        log.info(msg)
        if self._log_callback:
            self._log_callback(msg)

    def _progress(self, pct: int, msg: str = ""):
        self._current_progress = pct
        if self._progress_callback:
            self._progress_callback(pct, msg)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o consolidador com os parâmetros fornecidos.
        
        params:
            input_files: List[str] - arquivos a consolidar
            output_path: str - caminho do arquivo de saída
            merge_strategy: str = "concat" - "concat" | "merge" | "join"
            max_rows: Optional[int] = None
            sheet_selection: str = "first" - "first" | "all" | nome da aba
            enable_fuzzy_mapping: bool = True
            fuzzy_threshold: int = 80
            join_key: Optional[str] = None
            join_type: str = "left"
            visual_theme: str = "classic_blue"
            remove_duplicates: bool = False
            export_format: str = "xlsx" - "xlsx" | "parquet" | "csv"
        """
        try:
            self._progress(0, "Iniciando consolidação...")
            self._log("Iniciando consolidação de arquivos")
            
            result = self._engine.consolidate(
                input_files=params.get("input_files", []),
                output_path=params.get("output_path", ""),
                merge_strategy=params.get("merge_strategy", "concat"),
                max_rows=params.get("max_rows"),
                sheet_selection=params.get("sheet_selection", "first"),
                enable_fuzzy_mapping=params.get("enable_fuzzy_mapping", True),
                fuzzy_threshold=params.get("fuzzy_threshold", 80),
                join_key=params.get("join_key"),
                join_type=params.get("join_type", "left"),
                visual_theme=params.get("visual_theme", "classic_blue"),
                remove_duplicates=params.get("remove_duplicates", False),
                export_format=params.get("export_format", "xlsx"),
            )
            
            if result.get("success"):
                self._progress(100, "Concluído")
            
            return result
        except Exception as e:
            self._log(f"Erro na consolidação: {e}")
            return {"success": False, "error": str(e)}

    def get_progress(self) -> tuple[int, str]:
        return self._current_progress, ""

    def cancel(self):
        self._cancelled = True