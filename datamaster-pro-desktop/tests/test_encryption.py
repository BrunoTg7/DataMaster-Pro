import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.encryption import encrypt_data, decrypt_data, _derive_key

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
        decrypted = decrypt_data(encrypted, key2)
        
        assert decrypted == ""  # A implementação retorna "" em caso de erro

    def test_decryption_invalid_data(self):
        """Tentar descriptografar dados malformados ou não encriptados deve falhar."""
        assert decrypt_data("nao_sou_criptografado", "minha_chave") == ""
