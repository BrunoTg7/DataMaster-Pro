"""
Auth Manager - Supabase Authentication + Encryption
"""
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.encryption import encrypt_data, decrypt_data


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
            supabase: Client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_ANON_KEY
            )

            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.user:
                encrypted_password = encrypt_data(password)
                
                # Garantir que o usuário existe na tabela pública 'usuarios'
                profile = self._ensure_user_profile(response.user, response.session.access_token)
                
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "plan": profile.get("plano_tipo", "gratis"),
                    "created_at": profile.get("created_at"),
                    "notificacoes_email": profile.get("notificacoes_email", True),
                    "notificacoes_desktop": profile.get("notificacoes_desktop", True),
                    "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
                    "session_token": response.session.access_token,
                    "password_encrypted": encrypted_password
                }
                self.current_user = user_data
                self._session_token = response.session.access_token
                self._stored_credentials = {"email": email, "password": password}
                return {"success": True, "user": user_data}

        except Exception as e:
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "Login failed"}

    def _get_user_plan(self, user_id: str, token: str = None) -> str:
        """
        Fetch user plan from database
        """
        try:
            from supabase import create_client
            supabase = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
            if token:
                supabase.postgrest.auth(token)
                
            response = supabase.table("usuarios").select("plano_tipo").eq("id", user_id).execute()
            if response.data:
                return response.data[0].get("plano_tipo", "gratis")
        except:
            pass
        return "gratis"

    def _ensure_user_profile(self, auth_user, token: str) -> Dict:
        """Garante que o perfil do usuário existe e verifica o vínculo de hardware (HWID)"""
        try:
            from src.core.security.security_manager import SecurityManager
            current_hwid = SecurityManager.get_hwid()
            
            from supabase import create_client
            supabase = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
            supabase.postgrest.auth(token)
            
            # Buscar perfil
            res = supabase.table("usuarios").select("*").eq("id", auth_user.id).execute()
            
            if res.data:
                profile = res.data[0]
                stored_hwid = profile.get("hwid")
                
                # Se não houver HWID no banco, vinculamos este computador
                if not stored_hwid:
                    supabase.table("usuarios").update({"hwid": current_hwid}).eq("id", auth_user.id).execute()
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
                insert_res = supabase.table("usuarios").insert(new_profile).execute()
                return insert_res.data[0] if insert_res.data else new_profile
                
        except ValueError as ve:
            raise ve
        except Exception as e:
            print(f"[AUTH] Erro ao garantir perfil: {e}")
            return {"plano_tipo": "gratis", "created_at": datetime.now().isoformat()}

    def get_current_user(self) -> Optional[Dict]:
        return self.current_user

    def set_current_user(self, user_data: Dict):
        self.current_user = user_data

    def logout(self):
        self.current_user = None
        self._session_token = None

    def login_with_session(self, session_token: str) -> Dict:
        """
        Authenticate user via session token
        """
        if not session_token:
            return {"success": False, "error": "No session token"}

        try:
            from supabase import create_client, Client
            supabase: Client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_ANON_KEY
            )

            response = supabase.auth.refresh_session(session_token)

            if response.user:
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "plan": self._get_user_plan(response.user.id),
                    "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
                    "session_token": response.session.access_token
                }
                self.current_user = user_data
                self._session_token = response.session.access_token
                return {"success": True, "user": user_data}

        except Exception as e:
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "Session refresh failed"}

    def login_with_stored_credentials(self) -> Dict:
        """
        Re-authenticate using stored email/password when session expires
        """
        if not self._stored_credentials:
            return {"success": False, "error": "No stored credentials"}

        return self.login(
            self._stored_credentials["email"],
            self._stored_credentials["password"]
        )

    def is_session_valid(self) -> bool:
        if not self.current_user:
            return False

        expires_at = self.current_user.get("expires_at")
        if expires_at:
            try:
                exp_date = datetime.fromisoformat(expires_at)
                return exp_date > datetime.now()
            except:
                return False
        return True

    def refresh_session(self) -> bool:
        """
        Refresh session token silently
        """
        if not self._session_token:
            return False

        try:
            from supabase import create_client
            supabase = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_ANON_KEY
            )
            response = supabase.auth.refresh_session(self._session_token)
            if response.session:
                self._session_token = response.session.access_token
                self.current_user["session_token"] = response.session.access_token
                return True
        except:
            pass
        return False