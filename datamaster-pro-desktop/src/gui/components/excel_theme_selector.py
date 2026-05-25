import customtkinter as ctk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.excel_styler import THEME_NAMES, THEME_NAMES_REVERSE


class ExcelThemeSelector(ctk.CTkFrame):
    def __init__(self, master, tool_key: str, storage=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.tool_key = tool_key
        self._storage = storage

        lbl = ctk.CTkLabel(
            self,
            text="Tema Visual da Planilha (Excel):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        lbl.pack(anchor="w", pady=(5, 5))

        self._menu = ctk.CTkOptionMenu(
            self,
            values=list(THEME_NAMES.values()),
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER,
            command=self._on_change
        )
        self._menu.pack(fill="x", pady=(0, 10))

        self._load()

    def _load(self):
        saved = None
        if self._storage:
            saved = self._storage.get_tool_theme(self.tool_key)
        friendly = THEME_NAMES.get(saved, "Azul Corporativo")
        self._menu.set(friendly)

    def _on_change(self, choice):
        theme_key = THEME_NAMES_REVERSE.get(choice, "classic_blue")
        if self._storage:
            self._storage.save_tool_theme(self.tool_key, theme_key)

    def get_theme_key(self) -> str:
        return THEME_NAMES_REVERSE.get(self._menu.get(), "classic_blue")

    def set_theme_key(self, theme_key: str):
        friendly = THEME_NAMES.get(theme_key, "Azul Corporativo")
        self._menu.set(friendly)
