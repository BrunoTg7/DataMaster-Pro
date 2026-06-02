"""
DataMaster Pro - Main Application Window
"""
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from typing import Optional, Dict
import sys
import os
import threading
import logging

log = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from src.core.auth.auth_manager import AuthManager
from src.core.storage.storage_manager import StorageManager
from src.core.sync.sync_manager import SyncManager, ExecutionTracker
from src.utils.network import check_internet_connection
from src.core.update.update_checker import check_update_on_start
from src.core.tasks.task_executor import task_executor
from src.tools.tool_registry import register_all_tools
from src.gui.components.task_bar import TaskBar
from src.gui.components.toast import ToastManager

TOOL_PAGE_MODULES = {
    "consolidador": "src.gui.pages.tools.consolidador_page",
    "categorizador": "src.gui.pages.tools.categorizador_page",
    "orcamentos": "src.gui.pages.tools.orcamentos_page",
    "minerador": "src.gui.pages.tools.minerador_page",
    "conciliador": "src.gui.pages.tools.conciliador_page",
    "validador_links": "src.gui.pages.tools.validador_links_page",
    "extrator_reviews": "src.gui.pages.tools.extrator_reviews_page",
    "calculadora_lucratividade": "src.gui.pages.tools.calculadora_lucratividade_page",
    "analista_tendencias": "src.gui.pages.tools.analista_tendencias_page",
    "data_sanitizer": "src.gui.pages.tools.data_sanitizer_page",
    "conversor_ocr": "src.gui.pages.tools.conversor_ocr_page",
    "gerador_laudos": "src.gui.pages.tools.gerador_laudos_page",
    "comissoes": "src.gui.pages.tools.comissoes_page",
    "classificador_ncm": "src.gui.pages.tools.classificador_ncm_page",
    "precificador_canal": "src.gui.pages.tools.precificador_canal_page",
}

TOOL_PAGE_CLASSES: Dict[str, type] = {}


class DataMasterApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        from src.core.security.security_manager import SecurityManager
        self._lock_socket = SecurityManager.check_instance_lock()
        if not self._lock_socket:
            from tkinter import messagebox
            import customtkinter as ctk_temp
            temp_root = ctk_temp.CTk()
            temp_root.withdraw()
            messagebox.showwarning("DataMaster Pro", "O aplicativo j\u00e1 est\u00e1 em execu\u00e7\u00e3o.\nPor favor, feche a inst\u00e2ncia anterior.")
            import sys as _sys
            _sys.exit(0)

        super().__init__()
        self.TkdndVersion = None

        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("datamasterpro.desktop")
        except Exception:
            pass

        try:
            self.TkdndVersion = TkinterDnD._require(self)
        except Exception as e:
            log.warning("Drag & Drop não pôde ser inicializado: %s", e)
            self.TkdndVersion = None

        self.title(config.APP_NAME)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.resizable(True, True)

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        icone_path = os.path.join(base_path, "assets", "datamaster.ico")
        if os.path.exists(icone_path):
            self.iconbitmap(icone_path)

        ctk.set_appearance_mode(config.THEME)
        ctk.set_default_color_theme("green")

        self.current_page: Optional[ctk.CTkFrame] = None
        self.auth_manager = AuthManager()
        self.storage_manager = StorageManager()
        self.sync_manager = SyncManager(self.storage_manager)
        self.execution_tracker = ExecutionTracker(self.storage_manager, self.sync_manager)

        task_executor.storage = self.storage_manager
        register_all_tools(task_executor)

        self._load_saved_theme()

        self.is_online = True
        self.after_id = None
        self._current_page_type = None
        self._current_page_params = {}
        self._sync_scheduled = False
        self._last_connection_change = 0
        self._connection_debounce_ms = 2000

        self._page_cache: Dict[str, ctk.CTkFrame] = {}
        self._page_cache_order: list = []
        self._max_cache_size = 3

        self._setup_layout()
        self.toast = ToastManager.get_instance(self)
        self._check_dependencies()
        self._start_connection_monitor()
        self._start_footer_poll()

        self.storage_manager.cleanup_old_tasks(days=7)
        self.storage_manager.cleanup_executions_duplicates()

        self._show_login()

        self.after(100, self._fix_taskbar)

    def _fix_taskbar(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_TOOLWINDOW
            style = style | WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass
        try:
            if self.winfo_exists():
                self.iconify()
                self.after(50, lambda: self.deiconify() if self.winfo_exists() else None)
        except Exception:
            pass

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.footer = ctk.CTkFrame(self, fg_color=config.Colors.CARD, height=40, corner_radius=0)
        self.footer.grid(row=1, column=0, sticky="ew")
        self.footer.grid_columnconfigure(4, weight=1)

        self.footer_status_led = ctk.CTkLabel(
            self.footer,
            text="\u25cf",
            font=ctk.CTkFont(size=16),
            text_color="#10B981"
        )
        self.footer_status_led.grid(row=0, column=0, padx=(20, 5), pady=10)

        self.footer_connection_label = ctk.CTkLabel(
            self.footer,
            text="Online",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.footer_connection_label.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.footer_task_label = ctk.CTkLabel(
            self.footer,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.footer_task_label.grid(row=0, column=2, padx=(0, 10), pady=10)

        self.footer_sync_label = ctk.CTkLabel(
            self.footer,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#10B981"
        )
        self.footer_sync_label.grid(row=0, column=3, padx=(0, 10), pady=10)

        self.footer_version_label = ctk.CTkLabel(
            self.footer,
            text=f"v{config.APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.footer_version_label.grid(row=0, column=5, padx=20, pady=10)

        self.task_bar = TaskBar(self, width=350, height=100)

    def _load_saved_theme(self):
        saved_theme = self.storage_manager.get_theme()
        if saved_theme and saved_theme != "system":
            ctk.set_appearance_mode(saved_theme)
            config.THEME = saved_theme
            config.Colors.update_from_theme(saved_theme)
        elif saved_theme == "system":
            config.THEME = "system"
            ctk_theme = ctk.get_appearance_mode()
            config.Colors.update_from_theme(ctk_theme)

    def _check_dependencies(self):
        missing_deps = []
        required = {
            "pandas": "pandas",
            "openpyxl": "openpyxl",
            "supabase": "supabase",
            "customtkinter": "customtkinter",
            "PIL": "Pillow",
            "bs4": "beautifulsoup4",
            "requests": "requests",
            "cryptography": "cryptography",
            "pypdf": "pypdf",
        }
        for import_name, package_name in required.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_deps.append(package_name)
        if missing_deps:
            from tkinter import messagebox
            messagebox.showerror(
                "Depend\u00eancias Faltando",
                f"Instale as depend\u00eancias faltantes:\n\npip install {' '.join(missing_deps)}"
            )

    def _start_connection_monitor(self):
        import queue
        self._conn_queue = queue.Queue()

        def _check_and_poll():
            # Processa resultados pendentes de execuções anteriores
            try:
                while True:
                    online = self._conn_queue.get_nowait()
                    self._on_connection_result(online)
            except queue.Empty:
                pass
            # Dispara nova verificação em background
            def _bg():
                try:
                    online = check_internet_connection()
                    self._conn_queue.put(online)
                except Exception:
                    pass
            threading.Thread(target=_bg, daemon=True).start()
            # Agenda próximo ciclo
            self.after(config.SYNC_INTERVAL_MS, _check_and_poll)

        # Primeiro ciclo imediato
        _check_and_poll()

    def _on_connection_result(self, online: bool):
        was_online = self.is_online
        self.is_online = online
        if was_online != self.is_online:
            self._on_connection_changed()
        else:
            self._update_footer()

    def _start_footer_poll(self):
        def poll():
            if hasattr(self, "footer") and self.footer.winfo_viewable():
                self._update_footer()
            self.after(5000, poll)
        poll()

    def _on_connection_changed(self):
        import time
        now = time.time()
        if (now - self._last_connection_change) < (self._connection_debounce_ms / 1000):
            return
        self._last_connection_change = now
        self._update_footer()
        if self.is_online:
            self.toast.success("Conexão restaurada", duration_ms=2000)
            if not self._sync_scheduled:
                self._sync_scheduled = True
                self.after(2000, self._do_sync)
        else:
            self.toast.warning("Conexão perdida - modo offline", duration_ms=3000)
        try:
            page = getattr(self, 'current_page', None)
            if page and page.winfo_exists():
                if hasattr(page, 'update_connection_status'):
                    page.update_connection_status(self.is_online)
        except Exception:
            pass

    def _do_sync(self):
        self._sync_scheduled = False
        def _sync_wrapper():
            try:
                result = self.sync_manager.sync_now()
                if result.get("success"):
                    self.after(0, lambda: self.toast.success("Dados sincronizados", duration_ms=2000))
                else:
                    log.warning(f"Sync parcial: {result.get('error', 'erro desconhecido')}")
            except Exception as e:
                log.error(f"Erro na sincronização: {e}")
        threading.Thread(target=_sync_wrapper, daemon=True).start()

    def _update_footer_theme(self):
        if hasattr(self, 'footer'):
            self.footer.configure(fg_color=config.Colors.CARD)
        if hasattr(self, 'footer_connection_label'):
            self.footer_connection_label.configure(text_color=config.Colors.TEXT_SECONDARY)
        if hasattr(self, 'footer_task_label'):
            self.footer_task_label.configure(text_color=config.Colors.TEXT_SECONDARY)
        if hasattr(self, 'footer_sync_label'):
            self.footer_sync_label.configure(text_color=config.Colors.TEXT_SECONDARY)
        if hasattr(self, 'footer_version_label'):
            self.footer_version_label.configure(text_color=config.Colors.TEXT_SECONDARY)

    def _update_footer(self):
        if hasattr(self, 'footer_status_led'):
            color = "#10B981" if self.is_online else "#EF4444"
            self.footer_status_led.configure(text_color=color)
            self.footer_connection_label.configure(text="Online" if self.is_online else "Offline")
        if hasattr(self, 'footer_task_label'):
            try:
                active = task_executor.get_active_tasks()
                count = len(active) if isinstance(active, list) else 0
                if count > 0:
                    self.footer_task_label.configure(
                        text=f"\u26a1 {count} ativa{'s' if count != 1 else ''}",
                        text_color=config.Colors.ALERT
                    )
                else:
                    self.footer_task_label.configure(text="", text_color=config.Colors.TEXT_SECONDARY)
            except Exception:
                self.footer_task_label.configure(text="", text_color=config.Colors.TEXT_SECONDARY)
        if hasattr(self, 'footer_sync_label'):
            if self.is_online:
                try:
                    stats = self.sync_manager.get_queue_stats() if self.sync_manager else {}
                    pending = stats.get("pending", 0)
                    if pending > 0:
                        self.footer_sync_label.configure(
                            text=f"\u2b06 {pending} pendente{'s' if pending != 1 else ''}",
                            text_color=config.Colors.ALERT
                        )
                    else:
                        self.footer_sync_label.configure(text="\u2713 Sincronizado", text_color="#10B981")
                except Exception:
                    self.footer_sync_label.configure(text="Sync: --", text_color=config.Colors.TEXT_SECONDARY)
            else:
                self.footer_sync_label.configure(text="\u23f8 Offline", text_color=config.Colors.TEXT_SECONDARY)

    _update_footer_connection = _update_footer

    def _hide_footer_and_taskbar(self):
        if hasattr(self, "footer"):
            self.footer.grid_remove()
        if hasattr(self, "task_bar"):
            self.task_bar.place_forget()

    def _restore_footer_and_taskbar(self):
        if hasattr(self, "footer"):
            self.footer.grid()
        if hasattr(self, "task_bar") and self.task_bar.winfo_exists():
            self.task_bar.place(relx=0, rely=1.0, anchor="sw", x=10, y=-50)
            self.task_bar.lift()
        elif hasattr(self, "task_bar"):
            self.task_bar.lift()

    def _show_login(self):
        self._hide_current_page()
        from src.gui.pages.login_page import LoginPage
        page = self._page_cache.get("login")
        if page and page.winfo_exists():
            self.current_page = page
            self.current_page.grid(row=0, column=0, sticky="nsew")
        else:
            self.current_page = LoginPage(
                master=self,
                on_login_success=self._on_login_success
            )
            self.current_page.grid(row=0, column=0, sticky="nsew")
            self._cache_page("login", self.current_page)
        self._hide_footer_and_taskbar()

    def _on_login_success(self, user_data: dict):
        self.auth_manager.set_current_user(user_data)
        from src.core.plan_limits_manager import update_plan_validator
        update_plan_validator(
            user_data.get("plan", "gratis"),
            data_expiracao=user_data.get("data_expiracao")
        )
        self._sync_theme()
        if not config.SESSION_UPDATE_CHECKED:
            def run_and_cache():
                config.LAST_UPDATE_DATA = check_update_on_start()
                config.SESSION_UPDATE_CHECKED = True
            threading.Thread(target=run_and_cache, daemon=True).start()
        threading.Thread(target=self._preload_tool_pages, daemon=True).start()
        self._show_dashboard()

    def _preload_tool_pages(self):
        for tool_key in list(TOOL_PAGE_MODULES.keys()):
            try:
                self._get_tool_page_class(tool_key)
            except Exception as e:
                log.error("Erro pré-carregando %s: %s", tool_key, e)

    def _sync_theme(self):
        try:
            user = self.auth_manager.get_current_user()
            if not user or not user.get("id"):
                return
            access_token = self.storage_manager.get_token()
            if not access_token:
                return
            from supabase import create_client
            _c = create_client(config._u0, config._r1())
            _c.postgrest.auth(access_token)
            result = _c.table("usuarios").select("preferencias_tema").eq("id", user["id"]).execute()
            if result.data and len(result.data) > 0 and isinstance(result.data[0], dict):
                remote_theme = result.data[0].get("preferencias_tema")
                if remote_theme:
                    local_theme = self.storage_manager.get_theme()
                    if not local_theme or local_theme == "system":
                        self.storage_manager.save_theme(remote_theme)
                        ctk.set_appearance_mode(remote_theme)
                        config.THEME = remote_theme
                        config.Colors.update_from_theme(remote_theme)
                        self._update_footer_theme()
                        if hasattr(self, 'task_bar') and self.task_bar.winfo_exists():
                            self.task_bar.update_colors()
        except Exception as e:
            log.error("Erro ao buscar tema remoto: %s", e)

    def _show_dashboard(self):
        self._hide_current_page()
        self._current_page_type = 'dashboard'
        self._current_page_params = {}
        from src.gui.pages.dashboard_page import DashboardPage
        page = self._page_cache.get("dashboard")
        if page and page.winfo_exists():
            self.current_page = page
            self.current_page.grid(row=0, column=0, sticky="nsew")
        else:
            self.current_page = DashboardPage(
                master=self,
                user_data=self.auth_manager.get_current_user(),
                on_logout=self._on_logout,
                on_open_tool=self._show_tool_page,
                is_online=self.is_online,
                sync_manager=self.sync_manager,
                execution_tracker=self.execution_tracker,
                on_settings=self._show_settings
            )
            self.current_page.grid(row=0, column=0, sticky="nsew")
            self._cache_page("dashboard", self.current_page)
        self._restore_footer_and_taskbar()
        self._update_footer()
        task_executor.recover_interrupted_tasks()
        from src.core.tasks.execution_history_manager import get_history_manager
        get_history_manager()._cleanup_old()
        self.storage_manager.cleanup_old_tasks(days=7)
        self.storage_manager.cleanup_executions_duplicates()

    def _get_tool_page_class(self, tool_key: str):
        if tool_key not in TOOL_PAGE_CLASSES:
            module_path = TOOL_PAGE_MODULES.get(tool_key)
            if not module_path:
                return None
            import importlib
            module = importlib.import_module(module_path)
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, ctk.CTkFrame):
                    TOOL_PAGE_CLASSES[tool_key] = obj
                    break
        return TOOL_PAGE_CLASSES.get(tool_key)

    def _show_tool_page(self, tool_key: str):
        page_class = self._get_tool_page_class(tool_key)
        if not page_class:
            return
        self._hide_current_page()
        self._current_page_type = 'tool'
        self._current_page_params = {'tool_key': tool_key}
        cache_key = f"tool_{tool_key}"
        page = self._page_cache.get(cache_key)
        if page and page.winfo_exists():
            self.current_page = page
            self.current_page.grid(row=0, column=0, sticky="nsew")
        else:
            user = self.auth_manager.get_current_user()
            user_id = user.get("id") if user else None
            self.current_page = page_class(
                master=self,
                on_back=self._show_dashboard,
                execution_tracker=self.execution_tracker,
                user_id=user_id
            )
            self.current_page.grid(row=0, column=0, sticky="nsew")
            self._cache_page(cache_key, self.current_page)
        self._restore_footer_and_taskbar()
        self._update_footer()

    def _on_logout(self):
        self.auth_manager.logout()
        self.storage_manager.clear_session()
        self._clear_page_cache()
        self._show_login()

    def _show_settings(self):
        self._hide_current_page()
        self._current_page_type = 'settings'
        self._current_page_params = {}
        from src.gui.pages.settings_page import SettingsPage
        page = self._page_cache.get("settings")
        if page and page.winfo_exists():
            self.current_page = page
            self.current_page.grid(row=0, column=0, sticky="nsew")
        else:
            self.current_page = SettingsPage(
                master=self,
                on_back=self._show_dashboard,
                on_logout=self._on_logout,
                auth_manager=self.auth_manager,
                storage_manager=self.storage_manager,
                execution_tracker=self.execution_tracker,
                sync_manager=self.sync_manager,
                on_theme_changed=self._on_theme_changed
            )
            self.current_page.grid(row=0, column=0, sticky="nsew")
            self._cache_page("settings", self.current_page)
        self._restore_footer_and_taskbar()

    def _on_theme_changed(self):
        if not self._current_page_type:
            return
        theme = config.THEME
        config.Colors.update_from_theme(theme)
        self._update_footer_theme()
        if hasattr(self, 'task_bar') and self.task_bar.winfo_exists():
            self.task_bar.update_colors()
        old_page = self.current_page
        old_cache = dict(self._page_cache)
        old_cache_order = list(self._page_cache_order)
        self._page_cache.clear()
        self._page_cache_order.clear()
        page_type = self._current_page_type
        params = self._current_page_params
        if page_type == 'dashboard':
            self._show_dashboard()
        elif page_type == 'tool':
            self._show_tool_page(params.get('tool_key'))
        elif page_type == 'settings':
            self._show_settings()
        for key, page in old_cache.items():
            if page and page.winfo_exists() and page is not old_page:
                try:
                    page.destroy()
                except Exception:
                    pass

    def _cache_page(self, key: str, page: ctk.CTkFrame):
        self._page_cache[key] = page
        if key in self._page_cache_order:
            self._page_cache_order.remove(key)
        self._page_cache_order.append(key)
        if len(self._page_cache_order) > self._max_cache_size:
            oldest = self._page_cache_order.pop(0)
            old_page = self._page_cache.pop(oldest, None)
            if old_page and old_page.winfo_exists():
                old_page.destroy()

    def _clear_page_cache(self):
        for page in self._page_cache.values():
            if page and page.winfo_exists():
                try:
                    page.destroy()
                except Exception:
                    pass
        self._page_cache.clear()
        self._page_cache_order.clear()

    def _hide_current_page(self):
        if self.current_page and self.current_page.winfo_exists():
            self.current_page.grid_remove()

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = DataMasterApp()
    app.run()
