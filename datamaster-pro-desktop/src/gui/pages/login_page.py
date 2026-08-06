"""
Login Page - Authentication with Supabase
"""
import customtkinter as ctk
import sys
import os
import base64
import json
import threading
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.auth.auth_manager import AuthManager
from src.core.storage.storage_manager import StorageManager
from src.utils.network import check_internet_connection
from src.core.audit_logger import audit_lgpd_consent


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

        separator = ctk.CTkFrame(inner_frame, fg_color="transparent", height=20)
        separator.pack()
        or_label = ctk.CTkLabel(
            separator,
            text="ou",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        or_label.pack()

        self.google_button = ctk.CTkButton(
            inner_frame,
            text="Continuar com Google",
            width=320,
            height=45,
            fg_color="#ffffff",
            hover_color="#f5f5f5",
            text_color="#333333",
            font=ctk.CTkFont(family="Inter", size=14),
            corner_radius=8,
            border_width=1,
            border_color="#dadce0",
            command=self._on_google_login,
        )
        self.google_button.pack(pady=(10, 0))

        self.status_label = ctk.CTkLabel(
            inner_frame,
            text="",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=config.Colors.ALERT
        )
        self.status_label.pack(pady=(0, 15))

        register_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        register_frame.pack(pady=(0, 10))

        register_label = ctk.CTkLabel(
            register_frame,
            text="Não tem conta? ",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=config.Colors.TEXT_SECONDARY
        )
        register_label.pack(side="left")

        register_link = ctk.CTkLabel(
            register_frame,
            text="Cadastre-se aqui",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.PRIMARY,
            cursor="hand2"
        )
        register_link.pack(side="left")
        register_link.bind("<Button-1>", lambda e: self._open_register())

        # LGPD Consent
        self.consent_var = ctk.BooleanVar(value=False)
        self.consent_checkbox = ctk.CTkCheckBox(
            inner_frame,
            text="Li e aceito os Termos de Uso e a Politica de Privacidade. Consinto com o tratamento dos meus dados pessoais.",
            variable=self.consent_var,
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            corner_radius=4,
            border_width=1,
            border_color=config.Colors.BORDER,
            command=self._on_consent_change,
        )
        self.consent_checkbox.pack(pady=(10, 5), padx=20)

        self.consent_error_label = ctk.CTkLabel(
            inner_frame,
            text="",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color="#ef4444"
        )
        self.consent_error_label.pack(pady=(0, 5))

    def _is_session_valid_offline(self, saved_session: dict) -> bool:
        """Verifica se sessão é válida offline (janela de 15 dias).
        
        Em vez de checar o JWT real (expira em ~1h), verifica o campo
        expires_at da sessão salva com uma tolerância de 15 dias.
        Isso permite que o usuário use o app offline por até 15 dias
        após a última autenticação bem-sucedida.
        """
        expires_at = saved_session.get("expires_at")
        if not expires_at:
            return False
        try:
            exp_date = datetime.fromisoformat(expires_at)
            offline_grace = timedelta(days=15)
            return datetime.now() < exp_date + offline_grace
        except Exception:
            return False

    def _check_auto_login(self):
        saved_session = self.storage_manager.get_saved_session()
        if not saved_session:
            return

        online = check_internet_connection()

        if not online:
            # ── Modo offline: validar sessão localmente (sem rede) ──
            session_token = saved_session.get("session_token", "")
            if saved_session.get("id") and session_token:
                if self._is_session_valid_offline(saved_session):
                    self.after(100, lambda: self.on_login_success(saved_session))
                else:
                    self.status_label.configure(
                        text="Sessão expirada. Conecte-se à internet para reautenticar."
                    )
            return

        # ── Modo online: usar refresh_token para renovar sessão ──
        refresh_token = saved_session.get("refresh_token", "")
        if not refresh_token:
            return

        self.status_label.configure(text="Entrando automaticamente...")
        self.login_button.configure(state="disabled", text="Entrando...")

        try:
            result = self.auth_manager.login_with_session(refresh_token)
            if result.get("success"):
                user_data = result.get("user")
                self.storage_manager.save_user_session(user_data)
                self.after(100, lambda: self.on_login_success(user_data))
                return
            else:
                # Se o refresh token é inválido, limpar sessão salva
                if result.get("session_expired"):
                    self.storage_manager.clear_session()
                self.status_label.configure(text=result.get("error", "Sessão expirada. Faça login novamente."))
        except Exception as e:
            self.status_label.configure(text="Erro inesperado. Tente novamente.")
        finally:
            if self.login_button.winfo_exists():
                self.login_button.configure(state="normal", text="Entrar")

    def _on_consent_change(self):
        self.consent_error_label.configure(text="")

    def _on_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not self.consent_var.get():
            self.consent_error_label.configure(
                text="Voce deve aceitar os Termos de Uso e a Politica de Privacidade."
            )
            return

        if not email or not password:
            self.status_label.configure(text="Preencha todos os campos")
            return

        self.login_button.configure(state="disabled", text="Entrando...")
        self.status_label.configure(text="")

        try:
            result = self.auth_manager.login(email, password)
            if result.get("success"):
                user_data = result.get("user")
                self.storage_manager.save_user_session(user_data)
                self.storage_manager.save_consent(user_data["id"], True)
                audit_lgpd_consent(user_data["id"], True, "login_checkbox")
                self.after(100, lambda: self.on_login_success(user_data))
            else:
                self.status_label.configure(text=result.get("error", "Erro ao fazer login"))
        except Exception as e:
            self.status_label.configure(text="Erro inesperado. Tente novamente.")
        finally:
            if self.login_button.winfo_exists():
                self.login_button.configure(state="normal", text="Entrar")

    def _on_google_login(self):
        """Iniciar login com Google em thread separada"""
        if not self.consent_var.get():
            self.consent_error_label.configure(
                text="Voce deve aceitar os Termos de Uso e a Politica de Privacidade."
            )
            return

        self.google_button.configure(state="disabled", text="Abrindo navegador...")
        self.status_label.configure(text="")

        def google_auth_thread():
            try:
                result = self.auth_manager.login_with_google()
                if result.get("success"):
                    user_data = result.get("user")
                    self.storage_manager.save_user_session(user_data)
                    self.storage_manager.save_consent(user_data["id"], True)
                    audit_lgpd_consent(user_data["id"], True, "google_oauth")
                    self.after(100, lambda: self.on_login_success(user_data))
                else:
                    error_msg = result.get("error", "Erro ao autenticar com Google")
                    self.after(0, lambda: self.status_label.configure(text=error_msg))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(text="Erro inesperado. Tente novamente."))
            finally:
                if self.google_button.winfo_exists():
                    self.after(0, lambda: self.google_button.configure(
                        state="normal", text="Continuar com Google"
                    ))

        threading.Thread(target=google_auth_thread, daemon=True).start()

    def _open_register(self):
        import webbrowser
        webbrowser.open("https://data-master-pro.vercel.app/auth/registro")
