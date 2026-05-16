"""
Settings Page - Configurações do Aplicativo
"""
import customtkinter as ctk
from tkinter import filedialog
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.auth.auth_manager import AuthManager
from src.core.storage.storage_manager import StorageManager
from src.utils.network import check_internet_connection
from tkinter import messagebox


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, on_back, on_logout, auth_manager: AuthManager, storage_manager: StorageManager, execution_tracker=None, sync_manager=None, on_theme_changed=None):
        super().__init__(master)
        
        self.on_back = on_back
        self.on_logout = on_logout
        self.auth_manager = auth_manager
        self.storage_manager = storage_manager
        self.execution_tracker = execution_tracker
        self.sync_manager = sync_manager
        self.on_theme_changed = on_theme_changed
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_widgets()
    
    def _create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(
            header_frame,
            text="← Voltar",
            command=self.on_back,
            width=100,
            height=32,
            fg_color="transparent",
            hover_color=config.Colors.BORDER,
            border_width=1,
            border_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Inter", size=13),
            corner_radius=8
        ).grid(row=0, column=0, sticky="w")
        
        ctk.CTkLabel(
            header_frame,
            text="Configurações",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).grid(row=0, column=1, sticky="e", padx=10)
        
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.appearance_frame(scroll_frame)
        self.storage_frame(scroll_frame)
        self.account_frame(scroll_frame)
        self.about_frame(scroll_frame)
    
    def appearance_frame(self, parent):
        frame = ctk.CTkFrame(
            parent, 
            fg_color=config.Colors.CARD,
            border_width=1,
            border_color=config.Colors.BORDER,
            corner_radius=12
        )
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 20), padx=0)
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            frame,
            text="🎨 Aparência",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(
            frame,
            text="Escolha como o software deve se comportar visualmente:",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=config.Colors.TEXT_SECONDARY
        ).grid(row=1, column=0, sticky="w", padx=25, pady=(0, 15))
        
        self.theme_var = ctk.StringVar(value=config.THEME.lower())
        
        theme_grid = ctk.CTkFrame(frame, fg_color="transparent")
        theme_grid.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 25))
        
        # Opções de Tema
        themes = [
            ("☀️ Claro", "light"),
            ("🌙 Escuro", "dark"),
            ("🖥️ Sistema", "system")
        ]
        
        for i, (label, value) in enumerate(themes):
            ctk.CTkRadioButton(
                theme_grid,
                text=label,
                variable=self.theme_var,
                value=value,
                command=self._change_theme,
                font=ctk.CTkFont(family="Inter", size=14),
                fg_color=config.Colors.PRIMARY,
                hover_color=config.Colors.PRIMARY_HOVER
            ).grid(row=0, column=i, padx=15)
    
    def storage_frame(self, parent):
        frame = ctk.CTkFrame(
            parent, 
            fg_color=config.Colors.CARD,
            border_width=1,
            border_color=config.Colors.BORDER,
            corner_radius=12
        )
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 20), padx=0)
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            frame,
            text="📁 Arquivos",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(
            frame,
            text=f"Diretório de Dados: {config.APP_DATA_DIR}",
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        ).grid(row=1, column=0, sticky="w", padx=20)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="w", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text="📂 Alterar Diretório",
            command=self._change_output_dir,
            fg_color=config.Colors.CARD,
            hover_color=config.Colors.BORDER
        ).grid(row=0, column=0, padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🗑️ Limpar Cache",
            command=self._clear_cache,
            fg_color="#dc2626",
            hover_color="#b91c1c"
        ).grid(row=0, column=1, padx=5)
    
    def account_frame(self, parent):
        frame = ctk.CTkFrame(
            parent, 
            fg_color=config.Colors.CARD,
            border_width=1,
            border_color=config.Colors.BORDER,
            corner_radius=12
        )
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 20), padx=0)
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            frame,
            text="👤 Conta",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w", padx=25, pady=(20, 15))
        
        user = self.auth_manager.get_current_user()
        if user:
            ctk.CTkLabel(
                frame,
                text=f"Email: {user.get('email', 'Não informado')}",
                font=ctk.CTkFont(family="Inter", size=14),
                text_color=config.Colors.TEXT_PRIMARY
            ).grid(row=1, column=0, sticky="w", padx=25, pady=(0, 5))
            
            plan_name = user.get('plan', 'gratis').upper()
            ctk.CTkLabel(
                frame,
                text=f"Plano Atual: {plan_name}",
                font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                text_color=config.Colors.PRIMARY
            ).grid(row=2, column=0, sticky="w", padx=25, pady=2)

            # Cálculo de renovação
            created_at = user.get("created_at")
            if self.execution_tracker and created_at:
                from datetime import datetime, timedelta
                cycle_start = self.execution_tracker.get_current_cycle_start(created_at)
                # Próxima renovação (dia de aniversário no próximo mês)
                next_reset = cycle_start + timedelta(days=32)
                try:
                    day = datetime.fromisoformat(created_at.replace('Z', '+00:00')).day
                    next_reset = next_reset.replace(day=day)
                except: pass

                info_text = f"Próxima Renovação: {next_reset.strftime('%d/%m/%Y')}"
                if plan_name != "GRATIS":
                    info_text = f"Válido até: {next_reset.strftime('%d/%m/%Y')}"

                ctk.CTkLabel(
                    frame,
                    text=info_text,
                    font=ctk.CTkFont(family="Inter", size=12),
                    text_color=config.Colors.TEXT_SECONDARY
                ).grid(row=3, column=0, sticky="w", padx=25, pady=(2, 10))
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="w", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text="🚪 Sair da Conta",
            command=self._logout,
            fg_color="#dc2626",
            hover_color="#b91c1c"
        ).grid(row=0, column=0, padx=5)
    
    def about_frame(self, parent):
        frame = ctk.CTkFrame(
            parent, 
            fg_color=config.Colors.CARD,
            border_width=1,
            border_color=config.Colors.BORDER,
            corner_radius=12
        )
        frame.grid(row=3, column=0, sticky="ew", pady=(0, 20), padx=0)
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            frame,
            text="ℹ️ Sobre",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(
            frame,
            text=f"Versão: {config.APP_VERSION}",
            text_color=config.Colors.TEXT_SECONDARY
        ).grid(row=1, column=0, sticky="w", padx=20)
        
        ctk.CTkLabel(
            frame,
            text="DataMaster Pro © 2026",
            text_color=config.Colors.TEXT_SECONDARY
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(5, 10))
        
        ctk.CTkButton(
            frame,
            text="🔄 Verificar Atualizações",
            command=self._check_updates,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER
        ).grid(row=3, column=0, sticky="w", padx=20, pady=15)
    
    def _change_theme(self):
        theme = self.theme_var.get()
        import customtkinter as ctk
        ctk.set_appearance_mode(theme)
        config.THEME = theme
        config.Colors.update_from_theme(theme)
        
        self.storage_manager.save_theme(theme)
        
        if self.sync_manager:
            self.sync_manager.sync_theme_to_supabase(theme)
        
        if self.on_theme_changed:
            self.on_theme_changed()
    
    def _change_output_dir(self):
        directory = filedialog.askdirectory(title="Selecionar Diretório")
        if directory:
            messagebox.showinfo("Info", "Funcionalidade em desenvolvimento.")
    
    def _clear_cache(self):
        if messagebox.askyesno("Confirmar", "Deseja limpar o cache?"):
            import shutil
            try:
                shutil.rmtree(config.CACHE_DIR)
                os.makedirs(config.CACHE_DIR)
                messagebox.showinfo("Sucesso", "Cache limpo!")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
    
    def _logout(self):
        if messagebox.askyesno("Sair", "Deseja sair da conta?"):
            self.on_logout()
    
    def _check_updates(self):
        is_online = check_internet_connection()
        if is_online:
            messagebox.showinfo("Atualizações", f"Você está na versão mais recente: {config.APP_VERSION}")
        else:
            messagebox.showwarning("Sem Conexão", "Verifique sua internet.")