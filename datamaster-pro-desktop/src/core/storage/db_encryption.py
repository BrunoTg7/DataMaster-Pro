"""
DB Encryption - Criptografia de colunas do banco de dados.
Fornece criptografia AES (Fernet) para dados sensíveis com suporte a senha do usuário.

Camadas de segurança:
  1. Chave derivada do hardware (HWID) — trava o db nesta máquina
  2. Chave derivada da senha do usuário — trava sem a senha
  3. Fernet (AES-128-CBC + HMAC-SHA256) — criptografia autenticada
"""
import os
import base64
import hashlib
import json
import logging
from typing import Any, Optional, Set

from cryptography.fernet import Fernet, InvalidToken

log = logging.getLogger(__name__)

# ── Prefixo para identificar dados criptografados ──────────────────────────
ENC_PREFIX = "ENC$v1$"


class DBEncryptionError(Exception):
    pass


class DBEncryption:
    """
    Gerencia criptografia/descripgrafia de colunas do banco.

    Uso:
        enc = DBEncryption(password="minha_senha", hwid="ABC123...")
        encrypted = enc.encrypt("dados sensíveis")
        decrypted = enc.decrypt(encrypted)
    """

    def __init__(self, password: str = "", hwid: str = ""):
        self._password = password
        self._hwid = hwid
        self._fernet = self._derive_fernet()

    def _derive_fernet(self) -> Fernet:
        """Deriva chave Fernet a partir de senha + HWID."""
        material = f"{self._password}:{self._hwid}".encode("utf-8")
        digest = hashlib.sha256(material).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """Criptografa uma string. Retorna ciphertext com prefixo."""
        if not data:
            return ""
        try:
            encrypted = self._fernet.encrypt(data.encode("utf-8")).decode("utf-8")
            return f"{ENC_PREFIX}{encrypted}"
        except Exception as e:
            raise DBEncryptionError(f"Falha ao criptografar: {e}")

    def decrypt(self, data: str) -> str:
        """Descriptografa uma string. Suporta dados criptografados (com prefixo) e legados (sem prefixo)."""
        if not data:
            return ""
        try:
            if data.startswith(ENC_PREFIX):
                ciphertext = data[len(ENC_PREFIX):]
                return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
            else:
                return data
        except InvalidToken:
            raise DBEncryptionError("Token inválido — dados corrompidos ou chave incorreta")
        except Exception as e:
            raise DBEncryptionError(f"Falha ao descriptografar: {e}")

    def is_encrypted(self, data: str) -> bool:
        """Verifica se uma string já está criptografada."""
        return bool(data) and data.startswith(ENC_PREFIX)

    def encrypt_json(self, obj: Any) -> str:
        """Serializa JSON e criptografa."""
        return self.encrypt(json.dumps(obj, ensure_ascii=False))

    def decrypt_json(self, data: str) -> Any:
        """Descriptografa e deserializa JSON."""
        if not data:
            return None
        raw = self.decrypt(data)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw


# ── Senha do banco de dados ────────────────────────────────────────────────
DB_PASSWORD_FILE = ".db_password"


def get_or_create_db_password(db_dir: str) -> str:
    """
    Retorna ou cria a senha do banco.
    A senha é gerada uma vez e salva em arquivo oculto.
    """
    password_path = os.path.join(db_dir, DB_PASSWORD_FILE)
    if os.path.exists(password_path):
        try:
            with open(password_path, "r") as f:
                return f.read().strip()
        except OSError:
            pass
    # Gerar senha aleatória de 64 caracteres hex
    password = os.urandom(32).hex()
    try:
        with open(password_path, "w") as f:
            f.write(password)
        # Tornar oculto no Windows
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(password_path, 0x02)
        except Exception:
            pass
        log.info("Senha do banco gerada: %s", password_path)
    except OSError as e:
        log.warning("Não foi possível salvar senha do banco: %s", e)
    return password


def get_db_password(db_dir: str) -> str:
    """Retorna a senha do banco existente ou string vazia."""
    password_path = os.path.join(db_dir, DB_PASSWORD_FILE)
    if os.path.exists(password_path):
        try:
            with open(password_path, "r") as f:
                return f.read().strip()
        except OSError:
            pass
    return ""


# ── Helper para migração ──────────────────────────────────────────────────
def needs_encryption(data: str) -> bool:
    """Verifica se um dado NÃO está criptografado e precisa ser."""
    return bool(data) and not data.startswith(ENC_PREFIX)
