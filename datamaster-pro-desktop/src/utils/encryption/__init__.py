"""
Encryption Utilities - AES encryption for local storage with HWID support
"""
from cryptography.fernet import Fernet, InvalidToken
import os
import base64
import hashlib


class DecryptionError(Exception):
    """Erro de descriptografia - dados corrompidos ou chave inválida"""
    pass


def _derive_key(key_str: str) -> bytes:
    """Deriva uma chave Fernet válida a partir de qualquer string"""
    digest = hashlib.sha256(key_str.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_data(data: str, key: str) -> str:
    if not data:
        return ""
    cipher = Fernet(_derive_key(key))
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str, key: str) -> str:
    if not encrypted_data:
        return ""
    try:
        cipher = Fernet(_derive_key(key))
        return cipher.decrypt(encrypted_data.encode()).decode()
    except InvalidToken:
        raise DecryptionError("Token de criptografia inválido - dados podem estar corrompidos ou chave incorreta")
    except Exception as e:
        raise DecryptionError(f"Erro de descriptografia: {e}")
