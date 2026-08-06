import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.encryption import encrypt_data, decrypt_data, _derive_key, DecryptionError
from src.core.storage.db_encryption import DBEncryption, DBEncryptionError, ENC_PREFIX, needs_encryption

class TestEncryption:
    """Testes unitários para o módulo de criptografia."""

    def test_derive_key_consistent(self):
        """A derivação da chave deve ser sempre a mesma para a mesma string."""
        key_str = "minha-chave-secreta-123"
        derived1 = _derive_key(key_str)
        derived2 = _derive_key(key_str)
        
        assert derived1 == derived2
        assert len(derived1) == 44  # Base64 encoded 32-byte sha256 -> 44 chars

    def test_derive_key_different(self):
        """Chaves diferentes devem gerar derivações diferentes."""
        assert _derive_key("chave1") != _derive_key("chave2")

    def test_encrypt_data_changes_content(self):
        """O conteúdo criptografado não deve ser igual ao original."""
        original = "senha_secreta"
        key = "minha_chave"
        encrypted = encrypt_data(original, key)
        
        assert encrypted != original
        assert encrypted != ""

    def test_encrypt_empty_data(self):
        """Criptografar dados vazios deve retornar string vazia."""
        assert encrypt_data("", "key") == ""
        assert encrypt_data(None, "key") == ""

    def test_decrypt_empty_data(self):
        """Descriptografar dados vazios deve retornar string vazia."""
        assert decrypt_data("", "key") == ""
        assert decrypt_data(None, "key") == ""

    def test_encryption_roundtrip(self):
        """Criptografar e descriptografar deve resultar na string original."""
        original = "senha_super_secreta_123!@#"
        key = "minha_chave_mestra"
        
        encrypted = encrypt_data(original, key)
        decrypted = decrypt_data(encrypted, key)
        
        assert decrypted == original

    def test_decryption_wrong_key(self):
        """Descriptografar com a chave errada deve falhar retornando string vazia."""
        original = "senha_super_secreta"
        key1 = "minha_chave_mestra"
        key2 = "chave_errada"
        
        encrypted = encrypt_data(original, key1)
        with pytest.raises(DecryptionError):
            decrypt_data(encrypted, key2)

    def test_decryption_invalid_data(self):
        """Tentar descriptografar dados malformados ou não encriptados deve falhar."""
        with pytest.raises(DecryptionError):
            decrypt_data("nao_sou_criptografado", "minha_chave")


class TestDBEncryption:
    """Testes para o módulo de criptografia do banco de dados."""

    def test_encrypt_decrypt_roundtrip(self):
        """Criptografar e descriptografar deve retornar o original."""
        enc = DBEncryption(password="test-password-123", hwid="test-hwid-abc")
        original = "dados sensíveis do usuário"
        encrypted = enc.encrypt(original)
        decrypted = enc.decrypt(encrypted)
        assert decrypted == original

    def test_encrypted_has_prefix(self):
        """Dados criptografados devem começar com o prefixo ENC$v1$."""
        enc = DBEncryption(password="pw", hwid="hw")
        encrypted = enc.encrypt("test")
        assert encrypted.startswith(ENC_PREFIX)

    def test_encrypt_empty_returns_empty(self):
        """Criptografar string vazia retorna vazia."""
        enc = DBEncryption(password="pw", hwid="hw")
        assert enc.encrypt("") == ""
        assert enc.encrypt(None) == ""

    def test_decrypt_empty_returns_empty(self):
        """Descriptografar string vazia retorna vazia."""
        enc = DBEncryption(password="pw", hwid="hw")
        assert enc.decrypt("") == ""
        assert enc.decrypt(None) == ""

    def test_is_encrypted(self):
        """is_encrypted deve detectar dados criptografados."""
        enc = DBEncryption(password="pw", hwid="hw")
        assert enc.is_encrypted(enc.encrypt("test")) is True
        assert enc.is_encrypted("plain text") is False
        assert enc.is_encrypted("") is False

    def test_different_passwords_cannot_decrypt(self):
        """Chaves diferentes não devem conseguir descriptografar."""
        enc1 = DBEncryption(password="password1", hwid="hw")
        enc2 = DBEncryption(password="password2", hwid="hw")
        encrypted = enc1.encrypt("secret")
        with pytest.raises(DBEncryptionError):
            enc2.decrypt(encrypted)

    def test_different_hwids_cannot_decrypt(self):
        """HWIDs diferentes não devem conseguir descriptografar."""
        enc1 = DBEncryption(password="pw", hwid="hwid1")
        enc2 = DBEncryption(password="pw", hwid="hwid2")
        encrypted = enc1.encrypt("secret")
        with pytest.raises(DBEncryptionError):
            enc2.decrypt(encrypted)

    def test_encrypt_json_roundtrip(self):
        """Criptografar/descriptografar JSON deve funcionar."""
        enc = DBEncryption(password="pw", hwid="hw")
        data = {"key": "value", "number": 42, "nested": {"a": [1, 2, 3]}}
        encrypted = enc.encrypt_json(data)
        decrypted = enc.decrypt_json(encrypted)
        assert decrypted == data

    def test_decrypt_json_empty(self):
        """Descriptografar JSON vazio retorna None."""
        enc = DBEncryption(password="pw", hwid="hw")
        assert enc.decrypt_json("") is None
        assert enc.decrypt_json(None) is None

    def test_needs_encryption(self):
        """needs_encryption deve detectar dados não criptografados."""
        assert needs_encryption("plain text") is True
        assert needs_encryption(f"{ENC_PREFIX}encrypted") is False
        assert needs_encryption("") is False
        assert needs_encryption(None) is False

    def test_consistent_encryption_same_input(self):
        """Mesmos dados + mesma chave devem gerar criptografado diferente (Fernet é probabilístico)."""
        enc = DBEncryption(password="pw", hwid="hw")
        e1 = enc.encrypt("same input")
        e2 = enc.encrypt("same input")
        # Fernet gera ciphertext diferente a cada chamada (IV aleatório)
        assert e1 != e2
        # Mas ambos devem descriptografar para o mesmo valor
        assert enc.decrypt(e1) == "same input"
        assert enc.decrypt(e2) == "same input"

    def test_legacy_data_passthrough(self):
        """Dados legados (sem prefixo) devem passar direto no decrypt."""
        enc = DBEncryption(password="pw", hwid="hw")
        # Simular dado legado que não está criptografado
        assert enc.decrypt("legacy_plain_text") == "legacy_plain_text"
