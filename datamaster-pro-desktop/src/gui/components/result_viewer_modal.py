"""
Result Viewer Overlay Component - Visualização de resultados integrada à página
Corrigido para usar cores Hex compatíveis com CustomTkinter.
"""
import customtkinter as ctk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

class ResultViewerOverlay(ctk.CTkFrame):
    """Overlay interno para visualização de resultados com design premium"""
    
    def __init__(self, parent, title: str = "Relatório de Resultado", result_data: str = ""):
        # Cobrir toda a área do pai
        super().__init__(parent, fg_color="transparent")
        
        self.result_data = result_data
        self._setup_ui(title)

    def _setup_ui(self, title_text):
        # Background escuro sólido (Overlay) - Simula transparência no tema dark
        self.overlay = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Container Central (O "Card" do Resultado)
        self.modal_card = ctk.CTkFrame(
            self, 
            fg_color=config.Colors.CARD,
            border_width=1,
            border_color=config.Colors.BORDER,
            corner_radius=16
        )
        self.modal_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)
        
        # Grid para layout do card
        self.modal_card.grid_columnconfigure(0, weight=1)
        self.modal_card.grid_rowconfigure(1, weight=1)

        # Header do Modal
        header = ctk.CTkFrame(self.modal_card, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text=f"📋 {title_text}",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, sticky="w")

        close_btn = ctk.CTkButton(
            header,
            text="✕",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color="#333333",
            text_color=config.Colors.TEXT_SECONDARY,
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.close
        )
        close_btn.grid(row=0, column=1)

        # Área de Texto (Relatório)
        self.text_area = ctk.CTkTextbox(
            self.modal_card,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            border_width=1,
            border_color=config.Colors.BORDER,
            corner_radius=12
        )
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        self.text_area.insert("1.0", self.result_data)
        self.text_area.configure(state="disabled")

        # Footer
        footer = ctk.CTkFrame(self.modal_card, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 25))

        copy_btn = ctk.CTkButton(
            footer,
            text="📋 Copiar Tudo",
            width=140,
            height=38,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            command=self._copy_to_clipboard
        )
        copy_btn.pack(side="left", padx=5)

        done_btn = ctk.CTkButton(
            footer,
            text="Fechar",
            width=120,
            height=38,
            fg_color="transparent",
            border_width=1,
            border_color=config.Colors.BORDER,
            hover_color="#333333",
            font=ctk.CTkFont(family="Inter", size=13),
            command=self.close
        )
        done_btn.pack(side="right", padx=5)

    def _copy_to_clipboard(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.result_data)
            self._log_temp("Copiado!")
        except:
            pass

    def _log_temp(self, msg):
        # Implementação simples de feedback visual
        pass

    def close(self):
        self.destroy()


class ResultViewerButton(ctk.CTkButton):
    """Botão profissional que aciona o overlay de resultado"""
    
    def __init__(self, parent_page, container, get_result_callback, text: str = "📊 Visualizar Relatório"):
        # Cores Hex seguras
        super().__init__(
            container,
            text=text,
            width=220,
            height=40,
            fg_color="transparent",
            border_width=1,
            border_color=config.Colors.PRIMARY,
            text_color=config.Colors.PRIMARY,
            hover_color="#1f1f1f",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            corner_radius=8,
            command=self._show_overlay
        )
        self.parent_page = parent_page
        self.get_result_callback = get_result_callback

    def _show_overlay(self):
        result_text = self.get_result_callback()
        if not result_text or "aparecerão aqui" in result_text:
            return
            
        overlay = ResultViewerOverlay(self.parent_page, result_data=result_text)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)