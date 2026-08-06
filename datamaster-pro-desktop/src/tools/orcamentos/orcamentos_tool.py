"""
ITool Adapter for Orcamentos
"""
from src.tools.itool import ITool, register_tool
from src.tools.orcamentos.orcamentos import Orcamentos
from typing import Dict, Any, Optional
import logging

log = logging.getLogger(__name__)


@register_tool("orcamentos", "Orçamentos", "src.gui.pages.tools.orcamentos_page")
class OrcamentosTool(ITool):
    TOOL_KEY = "orcamentos"
    TOOL_NAME = "Orçamentos"
    TOOL_PAGE_MODULE = "src.gui.pages.tools.orcamentos_page"

    def __init__(self, progress_callback: Optional[callable] = None, log_callback: Optional[callable] = None):
        self._engine = Orcamentos()
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
        """Executa o gerador de orçamentos com os parâmetros fornecidos.
        
        params (generate_from_excel):
            data_file: str - arquivo de dados (xlsx, xls, csv)
            output_dir: str - diretório de saída
            watermark: bool = True
            watermark_text: str = "DataMaster Pro"
            config: Dict = {} - configuração completa do orçamento
        
        params (generate_from_excel_streaming):
            data_file: str
            output_dir: str
            watermark: bool = True
            watermark_text: str = "DataMaster Pro"
            config: Dict = {}
            batch_size: int = 50
        """
        try:
            self._progress(0, "Iniciando geração de orçamentos...")
            
            use_streaming = params.get("use_streaming", True)
            
            if use_streaming:
                result = self._engine.generate_from_excel_streaming(
                    data_file=params.get("data_file", ""),
                    output_dir=params.get("output_dir", ""),
                    watermark=params.get("watermark", True),
                    watermark_text=params.get("watermark_text", "DataMaster Pro"),
                    config=params.get("config", {}),
                    batch_size=params.get("batch_size", 50),
                )
            else:
                result = self._engine.generate_from_excel(
                    data_file=params.get("data_file", ""),
                    output_dir=params.get("output_dir", ""),
                    watermark=params.get("watermark", True),
                    watermark_text=params.get("watermark_text", "DataMaster Pro"),
                    config=params.get("config", {}),
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