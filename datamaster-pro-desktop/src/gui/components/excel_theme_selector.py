import customtkinter as ctk
import sys
import os
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.excel_styler import THEME_NAMES, THEME_NAMES_REVERSE
from src.core.plan_limits_manager import PlanLimitValidator


class ExcelThemeSelector(ctk.CTkFrame):
    def __init__(self, master, tool_key: str, storage=None, user_data=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.tool_key = tool_key
        self._storage = storage
        self.user_data = user_data or {}
        self.user_plan = self.user_data.get("plan", "gratis")
        
        # Criar validador de plano
        self._validator = PlanLimitValidator(self.user_plan)

        lbl = ctk.CTkLabel(
            self,
            text="Tema Visual da Planilha (Excel):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        lbl.pack(anchor="w", pady=(5, 5))

        # Se plano FREE, mostrar aviso
        if self.user_plan == "gratis":
            aviso_frame = ctk.CTkFrame(self, fg_color="transparent")
            aviso_frame.pack(anchor="w", pady=(0, 5))
            
            aviso_label = ctk.CTkLabel(
                aviso_frame,
                text="🔒 Tema único no plano Grátis (Azul Corporativo)",
                font=ctk.CTkFont(size=10),
                text_color="#F59E0B"
            )
            aviso_label.pack(anchor="w")
            
            upgrade_label = ctk.CTkLabel(
                aviso_frame,
                text="Upgrade para PRO para acessar 3 temas adicionais →",
                font=ctk.CTkFont(size=9),
                text_color=config.Colors.TEXT_SECONDARY
            )
            upgrade_label.pack(anchor="w")
        
        # Get available themes for this plan
        available_themes = self._validator.limits.get("available_themes", ["classic_blue"])
        theme_display_names = [
            THEME_NAMES.get(t, t) for t in available_themes
        ]

        self._menu = ctk.CTkOptionMenu(
            self,
            values=theme_display_names,
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER,
            command=self._on_change
        )
        self._menu.pack(fill="x", pady=(0, 10))
        
        # Se FREE, desabilitar menu
        if self.user_plan == "gratis":
            self._menu.configure(state="disabled")

        self._load()

    def _load(self):
        saved = None
        if self._storage:
            saved = self._storage.get_tool_theme(self.tool_key)
        friendly = THEME_NAMES.get(saved, "Azul Corporativo")
        self._menu.set(friendly)

    def _on_change(self, choice):
        theme_key = THEME_NAMES_REVERSE.get(choice, "classic_blue")
        
        # Validar acesso ao tema
        can_access, error_msg = self._validator.validate_theme_access(theme_key)
        
        if not can_access:
            messagebox.showwarning(
                "Acesso Restrito",
                f"{error_msg}\n\nUpgrade para PRO para desbloquear todos os temas."
            )
            # Reverter para tema padrão
            friendly = THEME_NAMES.get("classic_blue", "Azul Corporativo")
            self._menu.set(friendly)
            return
        
        if self._storage:
            self._storage.save_tool_theme(self.tool_key, theme_key)

    def get_theme_key(self) -> str:
        return THEME_NAMES_REVERSE.get(self._menu.get(), "classic_blue")

    def set_theme_key(self, theme_key: str):
        friendly = THEME_NAMES.get(theme_key, "Azul Corporativo")
        self._menu.set(friendly)
