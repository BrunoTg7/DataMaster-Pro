"""
ITool Adapter for Minerador Enterprise
"""
from src.tools.itool import ITool, register_tool
from src.tools.minerador.minerador_enterprise import MineradorEnterprise
from typing import Dict, Any, Optional
import logging

log = logging.getLogger(__name__)


@register_tool("minerador", "Minerador", "src.gui.pages.tools.minerador_page")
class MineradorTool(ITool):
    TOOL_KEY = "minerador"
    TOOL_NAME = "Minerador"
    TOOL_PAGE_MODULE = "src.gui.pages.tools.minerador_page"

    def __init__(self, progress_callback: Optional[callable] = None, log_callback: Optional[callable] = None):
        self._engine = MineradorEnterprise(
            progress_callback=progress_callback,
            log_callback=log_callback,
            max_concurrency=5,
        )
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
        """Executa o minerador com os parâmetros fornecidos.
        
        params:
            urls: List[str] - lista de URLs para minerar
            marketplace: str = "generico" - marketplace alvo
            custom_selectors: Dict[str, str] = {} - seletores customizados
            visual_theme: str = "classic_blue"
            max_successful: Optional[int] = None
            use_official_api: bool = True
        """
        try:
            self._progress(0, "Iniciando mineração...")
            
            result = self._engine.mine_from_links(
                urls=params.get("urls", []),
                marketplace=params.get("marketplace", "generico"),
                custom_selectors=params.get("custom_selectors", {}),
                visual_theme=params.get("visual_theme", "classic_blue"),
                max_successful=params.get("max_successful"),
                use_official_api=params.get("use_official_api", True),
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