"""
DataMaster Pro - Main Application Window
"""
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES, DND_ALL
from typing import Optional
import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from src.gui.pages.login_page import LoginPage
from src.gui.pages.dashboard_page import DashboardPage
from src.gui.pages.settings_page import SettingsPage
from src.gui.pages.tools.consolidador_page import ConsolidadorPage
from src.gui.pages.tools.categorizador_page import CategorizadorPage
from src.gui.pages.tools.orcamentos_page import OrcamentosPage
from src.gui.pages.tools.minerador_page import MineradorPage
from src.gui.pages.tools.conciliador_page import ConciliadorPage
from src.gui.pages.tools.validador_links_page import ValidadorLinksPage
from src.gui.pages.tools.extrator_reviews_page import ExtratorReviewsPage
from src.gui.pages.tools.calculadora_lucratividade_page import CalculadoraLucratividadePage
from src.gui.pages.tools.analista_tendencias_page import AnalistaTendenciasPage
from src.gui.pages.tools.data_sanitizer_page import DataSanitizerPage
from src.gui.pages.tools.conversor_ocr_page import ConversorOCRPage
from src.gui.pages.tools.gerador_laudos_page import GeradorLaudosPage
from src.gui.pages.tools.comissoes_page import ComissoesPage
from src.core.auth.auth_manager import AuthManager
from src.core.storage.storage_manager import StorageManager
from src.core.sync.sync_manager import SyncManager, ExecutionTracker
from src.utils.network import check_internet_connection
from src.core.update.update_checker import check_update_on_start


class DataMasterApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        # --- TRAVA DE SEGURANÇA (ANTI-CLONAGEM) ---
        from src.core.security.security_manager import SecurityManager
        self._lock_socket = SecurityManager.check_instance_lock()
        if not self._lock_socket:
            from tkinter import messagebox
            import customtkinter as ctk_temp
            # Cria uma janela temporária oculta apenas para o messagebox
            temp_root = ctk_temp.CTk()
            temp_root.withdraw()
            messagebox.showwarning("DataMaster Pro", "O aplicativo já está em execução.\nPor favor, feche a instância anterior.")
            import sys as _sys
            _sys.exit(0)
        # ------------------------------------------

        super().__init__()
        self.TkdndVersion = None
        
        try:
            self.TkdndVersion = TkinterDnD._require(self)
        except Exception as e:
            print(f"Aviso: Drag & Drop não pôde ser inicializado: {e}")
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
        
        self._load_saved_theme()

        self.is_online = True
        self.after_id = None
        self._current_page_type = None
        self._current_page_params = {}

        self._setup_layout()
        self._check_dependencies()
        self._start_connection_monitor()
        self._show_login()

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _load_saved_theme(self):
        """Carrega o tema salvo do storage ou usa o padrão do sistema"""
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
        """Verifica se todas as dependências estão instaladas"""
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
                "Dependências Faltando",
                f"Instale as dependências faltantes:\n\npip install {' '.join(missing_deps)}"
            )

    def _start_connection_monitor(self):
        """Monitora conexão em background"""
        def check_connection():
            was_online = self.is_online
            self.is_online = check_internet_connection()

            if was_online != self.is_online:
                self._on_connection_changed()

            self.after_id = self.after(config.SYNC_INTERVAL_MS, check_connection)

        check_connection()

    def _on_connection_changed(self):
        """Called when connection status changes"""
        if self.is_online:
            result = self.sync_manager.sync_now()
            if result.get("success"):
                print(f"Sincronizado {result.get('synced')} itens")

        if hasattr(self.current_page, 'update_connection_status'):
            self.current_page.update_connection_status(self.is_online)

    def _show_login(self):
        self._clear_current_page()
        self.current_page = LoginPage(
            master=self,
            on_login_success=self._on_login_success
        )
        self.current_page.grid(row=0, column=0, sticky="nsew")

    def _on_login_success(self, user_data: dict):
        self.auth_manager.set_current_user(user_data)
        self._sync_theme_from_supabase()
        
        # Verifica atualizações uma única vez após o login e guarda o resultado
        if not config.SESSION_UPDATE_CHECKED:
            def run_and_cache():
                from src.core.update.update_checker import check_update_on_start
                config.LAST_UPDATE_DATA = check_update_on_start()
                config.SESSION_UPDATE_CHECKED = True
            
            threading.Thread(target=run_and_cache, daemon=True).start()

        self._show_dashboard()
    
    def _sync_theme_from_supabase(self):
        """Busca o tema do Supabase e aplica localmente"""
        try:
            user = self.auth_manager.get_current_user()
            if not user or not user.get("id"):
                return
            
            access_token = self.storage_manager.get_token()
            if not access_token:
                return
            
            from supabase import create_client
            supabase = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
            supabase.postgrest.auth(access_token)
            
            result = supabase.table("usuarios").select("preferencias_tema").eq("id", user["id"]).execute()
            
            if result.data and len(result.data) > 0:
                remote_theme = result.data[0].get("preferencias_tema")
                if remote_theme:
                    local_theme = self.storage_manager.get_theme()
                    if not local_theme or local_theme == "system":
                        self.storage_manager.save_theme(remote_theme)
                        ctk.set_appearance_mode(remote_theme)
                        config.THEME = remote_theme
                        config.Colors.update_from_theme(remote_theme)
        except Exception as e:
            print(f"Erro ao buscar tema do Supabase: {e}")

    def _show_dashboard(self):
        self._clear_current_page()
        self._current_page_type = 'dashboard'
        self._current_page_params = {}
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
        
        # Forçar sincronização ao abrir se estiver online
        if self.is_online:
            threading.Thread(target=self.sync_manager.sync_now, daemon=True).start()

    def _show_tool_page(self, tool_key: str):
        page_classes = {
            "consolidador": ConsolidadorPage,
            "categorizador": CategorizadorPage,
            "orcamentos": OrcamentosPage,
            "minerador": MineradorPage,
            "conciliador": ConciliadorPage,
            "validador_links": ValidadorLinksPage,
            "extrator_reviews": ExtratorReviewsPage,
            "calculadora_lucratividade": CalculadoraLucratividadePage,
            "analista_tendencias": AnalistaTendenciasPage,
            "data_sanitizer": DataSanitizerPage,
            "conversor_ocr": ConversorOCRPage,
            "gerador_laudos": GeradorLaudosPage,
            "comissoes": ComissoesPage
        }

        page_class = page_classes.get(tool_key)
        if page_class:
            user = self.auth_manager.get_current_user()
            user_id = user.get("id") if user else None
            
            self._clear_current_page()
            self._current_page_type = 'tool'
            self._current_page_params = {'tool_key': tool_key}
            self.current_page = page_class(
                master=self,
                on_back=self._show_dashboard,
                execution_tracker=self.execution_tracker,
                user_id=user_id
            )
            self.current_page.grid(row=0, column=0, sticky="nsew")

    def _on_logout(self):
        self.auth_manager.logout()
        self.storage_manager.clear_session()
        self._show_login()

    def _show_settings(self):
        self._clear_current_page()
        self._current_page_type = 'settings'
        self._current_page_params = {}
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

    def _on_theme_changed(self):
        if not self._current_page_type:
            return
        
        theme = config.THEME
        config.Colors.update_from_theme(theme)
        
        page_type = self._current_page_type
        params = self._current_page_params
        
        if page_type == 'dashboard':
            self._show_dashboard()
        elif page_type == 'tool':
            self._show_tool_page(params.get('tool_key'))
        elif page_type == 'settings':
            self._show_settings()

    def _clear_current_page(self):
        if self.current_page:
            self.current_page.destroy()

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = DataMasterApp()
    app.run()