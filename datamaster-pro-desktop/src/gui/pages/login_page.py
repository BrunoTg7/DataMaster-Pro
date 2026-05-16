"""
Login Page - Authentication with Supabase
"""
import customtkinter as ctk
from tkinter import messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.auth.auth_manager import AuthManager
from src.core.storage.storage_manager import StorageManager
from src.utils.network import check_internet_connection


class LoginPage(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color=config.Colors.BACKGROUND)

        self.on_login_success = on_login_success
        self.auth_manager = AuthManager()
        self.storage_manager = StorageManager()

        self._setup_ui()
        self._check_auto_login()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(
            self, 
            fg_color=config.Colors.CARD,
            border_width=1,
            border_color=config.Colors.BORDER,
            corner_radius=16
        )
        container.grid(row=0, column=0)
        
        inner_frame = ctk.CTkFrame(container, fg_color="transparent")
        inner_frame.pack(padx=50, pady=50)

        title = ctk.CTkLabel(
            inner_frame,
            text=config.APP_NAME,
            font=ctk.CTkFont(family="Inter", size=32, weight="bold"),
            text_color=config.Colors.PRIMARY
        )
        title.pack(pady=(0, 10))

        subtitle = ctk.CTkLabel(
            inner_frame,
            text="Faça login para continuar",
            font=ctk.CTkFont(family="Inter", size=15),
            text_color=config.Colors.TEXT_SECONDARY
        )
        subtitle.pack(pady=(0, 40))

        self.email_entry = ctk.CTkEntry(
            inner_frame,
            width=320,
            height=45,
            placeholder_text="E-mail",
            font=ctk.CTkFont(family="Inter", size=14),
            corner_radius=8,
            border_width=1,
            border_color=config.Colors.BORDER,
            fg_color=config.Colors.BACKGROUND
        )
        self.email_entry.pack(pady=(0, 15))

        self.password_entry = ctk.CTkEntry(
            inner_frame,
            width=320,
            height=45,
            placeholder_text="Senha",
            show="*",
            font=ctk.CTkFont(family="Inter", size=14),
            corner_radius=8,
            border_width=1,
            border_color=config.Colors.BORDER,
            fg_color=config.Colors.BACKGROUND
        )
        self.password_entry.pack(pady=(0, 15))

        self.login_button = ctk.CTkButton(
            inner_frame,
            text="Entrar",
            width=320,
            height=45,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            corner_radius=8,
            command=self._on_login
        )
        self.login_button.pack(pady=(10, 20))

        self.status_label = ctk.CTkLabel(
            inner_frame,
            text="",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=config.Colors.ALERT
        )
        self.status_label.pack(pady=(0, 15))

    def _check_auto_login(self):
        saved_session = self.storage_manager.get_saved_session()
        if not saved_session:
            return

        if not check_internet_connection():
            return

        if not saved_session.get("password"):
            return

        self.status_label.configure(text="Entrando automaticamente...")
        self.login_button.configure(state="disabled", text="Entrando...")

        try:
            result = self.auth_manager.login(
                saved_session.get("email", ""),
                saved_session.get("password", "")
            )
            if result.get("success"):
                user_data = result.get("user")
                user_data["password"] = saved_session.get("password")
                self.storage_manager.save_user_session(user_data)
                self.on_login_success(user_data)
                return
            else:
                self.status_label.configure(text="Login falhou: " + result.get("error", ""))
        except Exception as e:
            self.status_label.configure(text="Erro: " + str(e))
        finally:
            if self.login_button.winfo_exists():
                self.login_button.configure(state="normal", text="Entrar")

    def _on_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            self.status_label.configure(text="Preencha todos os campos")
            return

        self.login_button.configure(state="disabled", text="Entrando...")
        self.status_label.configure(text="")

        try:
            result = self.auth_manager.login(email, password)
            if result.get("success"):
                user_data = result.get("user")
                user_data["password"] = password
                self.storage_manager.save_user_session(user_data)
                self.on_login_success(user_data)
            else:
                self.status_label.configure(text=result.get("error", "Erro ao fazer login"))
        except Exception as e:
            self.status_label.configure(text=f"Erro: {str(e)}")
        finally:
            if self.login_button.winfo_exists():
                self.login_button.configure(state="normal", text="Entrar")
