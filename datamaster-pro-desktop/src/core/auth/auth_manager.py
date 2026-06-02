"""
Auth Manager - Supabase Authentication + Encryption
"""
import json
import threading
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from typing import Optional, Dict
import sys
import os
import logging

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.audit_logger import audit_login, audit_logout
from src.core.session_context import set_user_id
# Removed encryption import as StorageManager handles encryption


class GoogleAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handler para capturar o callback do Google OAuth"""
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            GoogleAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<style>"
                "body{font-family:Inter,system-ui,sans-serif;text-align:center;padding:60px 20px;background:#f8fafc}"
                ".card{background:#fff;border-radius:16px;padding:40px;max-width:400px;margin:0 auto;box-shadow:0 4px 24px rgba(0,0,0,0.08)}"
                "h2{color:#16a34a;margin-bottom:8px;font-size:22px}"
                "p{color:#64748b;font-size:14px;line-height:1.6}"
                ".check{font-size:48px;margin-bottom:16px}"
                "</style></head><body>"
                "<div class='card'>"
                "<div class='check'>&#10003;</div>"
                "<h2>Autenticação concluída!</h2>"
                "<p>Pode fechar esta janela e voltar para o aplicativo.</p>"
                "</div></body></html>"
            )
            self.wfile.write(html.encode("utf-8"))
        elif "error" in params:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            error_msg = params.get("error_description", ["Erro desconhecido"])[0]
            self.wfile.write(f"<h1>Erro: {error_msg}</h1>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class AuthManager:
    def __init__(self):
        self.current_user: Optional[Dict] = None
        self._session_token: Optional[str] = None
        self._stored_credentials: Optional[Dict] = None

    def login(self, email: str, password: str) -> Dict:
        """
        Authenticate user via Supabase
        """
        try:
            from supabase import create_client, Client
            _c: Client = create_client(config._u0, config._r1())

            response = _c.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.user:
                profile = self._ensure_user_profile(response.user, response.session.access_token)
                # Garantir que profile é um dict
                if not isinstance(profile, dict):
                    profile = {"plano_tipo": "gratis"}
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "nome": profile.get("nome", (response.user.email or "usuario").split("@")[0]),
                    "plan": profile.get("plano_tipo", "gratis"),
                    "created_at": profile.get("created_at"),
                    "data_expiracao": profile.get("data_expiracao"),
                    "notificacoes_email": profile.get("notificacoes_email", True),
                    "notificacoes_desktop": profile.get("notificacoes_desktop", True),
                    "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
                    "session_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
                self.current_user = user_data
                self._session_token = response.session.access_token
                self._stored_credentials = {"refresh_token": response.session.refresh_token}
                set_user_id(user_data["id"])
                audit_login(user_data["id"], success=True)
                return {"success": True, "user": user_data}

        except Exception as e:
            audit_login(email, success=False, error=str(e))
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "Login failed"}

    def login_with_google(self) -> Dict:
        """
        Autenticar via Google OAuth usando loopback redirect.
        Abre o navegador do usuario e captura o callback em localhost.
        """
        try:
            from supabase import create_client, Client
            _c: Client = create_client(config._u0, config._r1())

            REDIRECT_PORT = 8765
            REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

            response = _c.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": REDIRECT_URI,
                }
            })

            if not response.url:
                return {"success": False, "error": "Falha ao gerar URL do Google"}

            # Extrair code_verifier do storage interno antes do redirect
            storage_key = _c.auth._storage_key
            code_verifier = _c.auth._storage.get_item(f"{storage_key}-code-verifier") or ""

            GoogleAuthCallbackHandler.auth_code = None

            def run_server():
                server = HTTPServer(("localhost", REDIRECT_PORT), GoogleAuthCallbackHandler)
                server.handle_request()
                server.server_close()

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            webbrowser.open(response.url)

            server_thread.join(timeout=120)

            if GoogleAuthCallbackHandler.auth_code is None:
                return {"success": False, "error": "Tempo esgotado ou autenticacao cancelada"}

            session_response = _c.auth.exchange_code_for_session({
                "auth_code": GoogleAuthCallbackHandler.auth_code,
                "code_verifier": code_verifier,
                "redirect_to": REDIRECT_URI,
            })

            if session_response.user:
                profile = self._ensure_user_profile(
                    session_response.user,
                    session_response.session.access_token
                )
                # Garantir que profile é um dict
                if not isinstance(profile, dict):
                    profile = {"plano_tipo": "gratis"}
                user_data = {
                    "id": session_response.user.id,
                    "email": session_response.user.email,
                    "nome": profile.get(
                        "nome",
                        (session_response.user.email or "usuario").split("@")[0]
                    ),
                    "plan": profile.get("plano_tipo", "gratis"),
                    "created_at": profile.get("created_at"),
                    "data_expiracao": profile.get("data_expiracao"),
                    "notificacoes_email": profile.get("notificacoes_email", True),
                    "notificacoes_desktop": profile.get("notificacoes_desktop", True),
                    "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
                    "session_token": session_response.session.access_token,
                    "refresh_token": session_response.session.refresh_token,
                }
                self.current_user = user_data
                self._session_token = session_response.session.access_token
                self._stored_credentials = {
                    "refresh_token": session_response.session.refresh_token
                }
                set_user_id(user_data["id"])
                audit_login(user_data["id"], success=True)
                return {"success": True, "user": user_data}

            return {"success": False, "error": "Falha ao obter sessao do Google"}

        except Exception as e:
            audit_login("google", success=False, error=str(e))
            return {"success": False, "error": str(e)}

    def _get_user_plan(self, user_id: str, token: str = None) -> str:
        """
        Fetch user plan from database
        """
        try:
            from supabase import create_client
            _c = create_client(config._u0, config._r1())
            if token:
                _c.postgrest.auth(token)
                
            response = _c.table("usuarios").select("plano_tipo").eq("id", user_id).execute()
            if response.data and isinstance(response.data[0], dict):
                return response.data[0].get("plano_tipo", "gratis")
        except Exception:
            pass
        return "gratis"

    def _get_user_profile(self, user_id: str, token: str = None) -> dict:
        """
        Fetch full user profile from database (plan + data_expiracao)
        """
        try:
            from supabase import create_client
            _c = create_client(config._u0, config._r1())
            if token:
                _c.postgrest.auth(token)

            response = _c.table("usuarios").select("plano_tipo, data_expiracao, created_at").eq("id", user_id).execute()
            if response.data and isinstance(response.data[0], dict):
                return response.data[0]
        except Exception:
            pass
        return {"plano_tipo": "gratis", "data_expiracao": None, "created_at": None}

    def _ensure_user_profile(self, auth_user, token: str) -> Dict:
        """Garante que o perfil do usuário existe e verifica o vínculo de hardware (HWID)"""
        try:
            from src.core.security.security_manager import SecurityManager
            current_hwid = SecurityManager.get_hwid()
            
            from supabase import create_client
            _c = create_client(config._u0, config._r1())
            _c.postgrest.auth(token)
            
            # Buscar perfil
            res = _c.table("usuarios").select("*").eq("id", auth_user.id).execute()
            
            if res.data and isinstance(res.data[0], dict):
                profile = res.data[0]
                stored_hwid = profile.get("hwid")
                
                # Se não houver HWID no banco, vinculamos este computador
                if not stored_hwid:
                    _c.table("usuarios").update({"hwid": current_hwid}).eq("id", auth_user.id).execute()
                    profile["hwid"] = current_hwid
                    return profile
                
                # Se houver HWID e for diferente, bloqueamos o acesso
                if stored_hwid != current_hwid:
                    raise ValueError("ACESSO BLOQUEADO: Esta licença está vinculada a outro dispositivo. Entre em contato com o suporte para transferir sua licença.")
                
                return profile
            else:
                # Criar perfil novo já com o HWID vinculado
                new_profile = {
                    "id": auth_user.id,
                    "email": auth_user.email,
                    "nome": auth_user.email.split("@")[0],
                    "plano_tipo": "gratis",
                    "hwid": current_hwid
                }
                insert_res = _c.table("usuarios").insert(new_profile).execute()
                if insert_res.data and isinstance(insert_res.data[0], dict):
                    return insert_res.data[0]
                return new_profile
                
        except ValueError as ve:
            raise ve
        except Exception as e:
            return {"plano_tipo": "gratis", "created_at": datetime.now().isoformat()}

    def get_current_user(self) -> Optional[Dict]:
        return self.current_user

    def set_current_user(self, user_data: Dict):
        self.current_user = user_data

    def logout(self):
        if self.current_user:
            audit_logout(self.current_user.get("id", "unknown"))
            set_user_id(None)
        self.current_user = None
        self._session_token = None

    def login_with_session(self, refresh_token: str) -> Dict:
        """
        Authenticate user via refresh token
        """
        if not refresh_token:
            return {"success": False, "error": "No session refresh token"}

        try:
            from supabase import create_client, Client
            _c: Client = create_client(config._u0, config._r1())

            response = _c.auth.refresh_session(refresh_token)

            if response.user:
                profile = self._ensure_user_profile(response.user, response.session.access_token)
                # Garantir que profile é um dict
                if not isinstance(profile, dict):
                    profile = {"plano_tipo": "gratis"}
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "nome": profile.get("nome", (response.user.email or "usuario").split("@")[0]),
                    "plan": profile.get("plano_tipo", "gratis"),
                    "created_at": profile.get("created_at"),
                    "data_expiracao": profile.get("data_expiracao"),
                    "notificacoes_email": profile.get("notificacoes_email", True),
                    "notificacoes_desktop": profile.get("notificacoes_desktop", True),
                    "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
                    "session_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
                self.current_user = user_data
                self._session_token = response.session.access_token
                self._stored_credentials = {"refresh_token": response.session.refresh_token}
                return {"success": True, "user": user_data}

        except Exception as e:
            error_msg = str(e)
            # Refresh token inválido ou não encontrado — limpar sessão local
            if "Refresh Token Not Found" in error_msg or "Invalid Refresh Token" in error_msg:
                logger.warning("Refresh token inválido/expirado, limpando sessão local")
                self._stored_credentials = None
                self._session_token = None
                self.current_user = None
                return {"success": False, "error": "Sessão expirada. Faça login novamente.", "session_expired": True}
            return {"success": False, "error": error_msg}

        return {"success": False, "error": "Session refresh failed"}

    def login_with_stored_credentials(self) -> Dict:
        """
        Re-authenticate using stored refresh_token when session expires
        """
        if not self._stored_credentials or not self._stored_credentials.get("refresh_token"):
            return {"success": False, "error": "No stored credentials"}

        return self.login_with_session(self._stored_credentials["refresh_token"])

    def is_session_valid(self) -> bool:
        if not self.current_user:
            return False

        expires_at = self.current_user.get("expires_at")
        if expires_at:
            try:
                exp_date = datetime.fromisoformat(expires_at)
                if exp_date <= datetime.now():
                    return False
            except Exception:
                return False

        return True

    def is_plan_expired(self) -> bool:
        """
        Verifica se o plano do usuário está expirado
        comparando data_expiracao com a data atual.
        Planos GRATIS nunca expiram por data.
        """
        if not self.current_user:
            return True

        plan = self.current_user.get("plan", "gratis")
        if plan == "gratis":
            return False

        data_expiracao = self.current_user.get("data_expiracao")
        if not data_expiracao:
            return False

        try:
            exp_date = datetime.fromisoformat(data_expiracao.replace("Z", "+00:00").replace(" ", "T"))
            agora = datetime.now(exp_date.tzinfo) if exp_date.tzinfo else datetime.now()
            return exp_date <= agora
        except Exception:
            return False

    def refresh_session(self) -> bool:
        """
        Refresh session token silently
        """
        if not self._session_token:
            return False

        try:
            from supabase import create_client
            _c = create_client(config._u0, config._r1())
            response = _c.auth.refresh_session(self._session_token)
            if response.session:
                self._session_token = response.session.access_token
                self.current_user["session_token"] = response.session.access_token
                return True
        except Exception:
            pass
        return False