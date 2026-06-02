"""
ToastManager - Sistema de notificações toast para a GUI
Exibe mensagens temporárias flutuantes no canto da janela.
"""
import customtkinter as ctk
import logging
from typing import Optional
from collections import deque

log = logging.getLogger(__name__)


class Toast(ctk.CTkFrame):
    """Componente individual de toast."""

    def __init__(self, parent, message: str, toast_type: str = "info", duration_ms: int = 3000):
        colors = {
            "info": ("#3B82F6", "#EFF6FF"),
            "success": ("#10B981", "#ECFDF5"),
            "warning": ("#F59E0B", "#FFFBEB"),
            "error": ("#EF4444", "#FEF2F2"),
        }
        border_color, fg_color = colors.get(toast_type, colors["info"])

        super().__init__(parent, fg_color=fg_color, corner_radius=10,
                         border_width=1, border_color=border_color)

        self.grid_columnconfigure(0, weight=1)

        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        icon = icons.get(toast_type, "ℹ️")

        self._label = ctk.CTkLabel(
            self,
            text=f"  {icon}  {message}",
            font=ctk.CTkFont(size=13),
            text_color="#1F2937",
            wraplength=350,
            anchor="w",
            justify="left",
        )
        self._label.grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        self._close_btn = ctk.CTkButton(
            self, text="✕", width=24, height=24,
            fg_color="transparent", hover_color="#D1D5DB",
            text_color="#6B7280", font=ctk.CTkFont(size=12),
            corner_radius=4, command=self._dismiss,
        )
        self._close_btn.grid(row=0, column=1, padx=(0, 8), pady=10)

        self._duration_ms = duration_ms
        self._after_id = None

    def show(self):
        """Agenda auto-dismiss e mostra o toast."""
        if self._duration_ms > 0:
            self._after_id = self.after(self._duration_ms, self._dismiss)

    def _dismiss(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        try:
            self.destroy()
        except Exception:
            pass


class ToastManager:
    """Gerencia pilha de toasts na janela principal."""

    _instance: Optional["ToastManager"] = None

    def __init__(self, root):
        self._root = root
        self._container: Optional[ctk.CTkFrame] = None
        self._queue: deque = deque()
        self._max_visible = 5

    @classmethod
    def get_instance(cls, root=None) -> "ToastManager":
        if cls._instance is None:
            if root is None:
                raise ValueError("Root necessário na primeira chamada")
            cls._instance = cls(root)
        return cls._instance

    def _ensure_container(self):
        if self._container is None or not self._container.winfo_exists():
            self._container = ctk.CTkFrame(self._root, fg_color="transparent")
            self._container.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=20)
            self._container.lift()

    def show(self, message: str, toast_type: str = "info", duration_ms: int = 3000):
        """Exibe um toast na tela."""
        self._ensure_container()

        # Limitar toasts visíveis
        children = self._container.winfo_children()
        if len(children) >= self._max_visible:
            try:
                children[0].destroy()
            except Exception:
                pass

        toast = Toast(self._container, message, toast_type, duration_ms)
        toast.pack(fill="x", pady=(0, 6))
        toast.show()
        toast.lift()

    def info(self, message: str, duration_ms: int = 3000):
        self.show(message, "info", duration_ms)

    def success(self, message: str, duration_ms: int = 3000):
        self.show(message, "success", duration_ms)

    def warning(self, message: str, duration_ms: int = 4000):
        self.show(message, "warning", duration_ms)

    def error(self, message: str, duration_ms: int = 5000):
        self.show(message, "error", duration_ms)
