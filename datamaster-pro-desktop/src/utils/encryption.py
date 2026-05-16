"""
Encryption Utilities - AES encryption for local storage
"""
from cryptography.fernet import Fernet
import os
import base64
import hashlib

_KEY_FILE = os.path.join(os.path.expanduser("~"), ".datamaster", ".key")


def _get_or_create_key():
    os.makedirs(os.path.dirname(_KEY_FILE), exist_ok=True)

    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            return f.read()

    key = Fernet.generate_key()
    with open(_KEY_FILE, "wb") as f:
        f.write(key)
    return key


_cipher = Fernet(_get_or_create_key())


def encrypt_data(data: str) -> str:
    if not data:
        return ""
    return _cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data:
        return ""
    try:
        return _cipher.decrypt(encrypted_data.encode()).decode()
    except:
        return ""