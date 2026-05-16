"""
Encryption Utilities - AES encryption for local storage with HWID support
"""
from cryptography.fernet import Fernet
import os
import base64
import hashlib

def _derive_key(key_str: str) -> bytes:
    """Deriva uma chave Fernet válida a partir de qualquer string"""
    # Usa SHA-256 para garantir 32 bytes e encoda em Base64
    digest = hashlib.sha256(key_str.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_data(data: str, key: str = None) -> str:
    """Criptografa dados usando a chave global ou uma chave personalizada"""
    if not data:
        return ""
    
    # Se não houver chave, usa uma padrão do sistema
    if not key:
        key = "datamaster-pro-default-key-2026"
    
    cipher = Fernet(_derive_key(key))
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str, key: str = None) -> str:
    """Descriptografa dados usando a chave global ou uma chave personalizada"""
    if not encrypted_data:
        return ""
    
    if not key:
        key = "datamaster-pro-default-key-2026"
        
    try:
        cipher = Fernet(_derive_key(key))
        return cipher.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return ""