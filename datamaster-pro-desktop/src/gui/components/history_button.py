"""
HistoryButton - Botão customizado para acessar histórico de execução de uma ferramenta
"""
import customtkinter as ctk
from src.gui.components.execution_history_modal import show_history_modal


class HistoryButton(ctk.CTkButton):
    """Botão profissional para abrir histórico de execução"""
    
    def __init__(self, master, tool_name: str, tool_display_name: str, **kwargs):
        """
        Args:
            master: Parent widget
            tool_name: Chave da ferramenta (ex: "consolidador")
            tool_display_name: Nome exibição (ex: "Consolidador")
        """
        self.tool_name = tool_name
        self.tool_display_name = tool_display_name
        
        # Configurações padrão
        default_config = {
            "text": "📋 Histórico",
            "font": ("Segoe UI", 11, "bold"),
            "text_color": "#ffffff",
            "fg_color": "#404040",
            "hover_color": "#505050",
            "height": 35,
            "command": self._open_history
        }
        
        # Sobrescrever com kwargs
        default_config.update(kwargs)
        
        super().__init__(master, **default_config)
    
    def _open_history(self):
        """Abre modal de histórico"""
        root = self.winfo_toplevel()
        show_history_modal(
            root,
            self.tool_name,
            self.tool_display_name
        )
