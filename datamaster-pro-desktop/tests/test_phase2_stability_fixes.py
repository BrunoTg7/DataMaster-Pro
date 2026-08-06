"""
Testes Phase 2 - Fixes de Estabilidade
- Sanitizador: email RFC 5322 + duplicatas
- Consolidador: cache fuzzy
- Conciliador: XML error tracking + progress callback
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSanitizerEmailValidation:
    """Testes de validação RFC 5322 do Sanitizador"""

    def _make_sanitizer(self):
        from src.tools.data_sanitizer.data_sanitizer_v2 import DataSanitizer
        return DataSanitizer()

    def test_valid_email_accepted(self):
        s = self._make_sanitizer()
        assert s._normalize_email("user@example.com") == "user@example.com"

    def test_valid_email_with_dots(self):
        s = self._make_sanitizer()
        assert s._normalize_email("first.last@company.com.br") == "first.last@company.com.br"

    def test_valid_email_with_plus(self):
        s = self._make_sanitizer()
        assert s._normalize_email("user+tag@domain.com") == "user+tag@domain.com"

    def test_valid_email_with_underscore(self):
        s = self._make_sanitizer()
        assert s._normalize_email("user_name@domain.com") == "user_name@domain.com"

    def test_valid_email_with_hyphen(self):
        s = self._make_sanitizer()
        assert s._normalize_email("user-name@my-domain.com") == "user-name@my-domain.com"

    def test_invalid_email_no_at(self):
        s = self._make_sanitizer()
        assert s._normalize_email("userexample.com") == ""

    def test_invalid_email_no_domain(self):
        s = self._make_sanitizer()
        assert s._normalize_email("user@") == ""

    def test_invalid_email_no_tld(self):
        s = self._make_sanitizer()
        assert s._normalize_email("user@domain") == ""

    def test_invalid_email_double_at(self):
        s = self._make_sanitizer()
        assert s._normalize_email("user@@domain.com") == ""

    def test_invalid_email_spaces(self):
        s = self._make_sanitizer()
        assert s._normalize_email("user @domain.com") == ""

    def test_empty_string(self):
        s = self._make_sanitizer()
        assert s._normalize_email("") == ""

    def test_none_value(self):
        s = self._make_sanitizer()
        assert s._normalize_email(None) == ""

    def test_nan_value(self):
        s = self._make_sanitizer()
        import math
        assert s._normalize_email(float('nan')) == ""

    def test_uppercase_lowered(self):
        s = self._make_sanitizer()
        assert s._normalize_email("USER@DOMAIN.COM") == "user@domain.com"

    def test_whitespace_trimmed(self):
        s = self._make_sanitizer()
        assert s._normalize_email("  user@domain.com  ") == "user@domain.com"


class TestSanitizerAbbreviations:
    """Testes de abreviação do Sanitizador (sem duplicatas)"""

    def _make_sanitizer(self):
        from src.tools.data_sanitizer.data_sanitizer_v2 import DataSanitizer
        return DataSanitizer()

    def test_avenida_abbreviation_single(self):
        s = self._make_sanitizer()
        result = s._normalize_address("AVENIDA PAULISTA")
        assert "AV." in result
        assert result.count("AV.") == 1

    def test_rua_abbreviation(self):
        s = self._make_sanitizer()
        result = s._normalize_address("RUA DAS FLORES")
        assert "R." in result

    def test_travessa_abbreviation(self):
        s = self._make_sanitizer()
        result = s._normalize_address("TRAVESSA DO COMERCIO")
        assert "TR." in result


class TestConsolidadorFuzzyCache:
    """Testes de cache fuzzy do Consolidador"""

    def _make_consolidador(self):
        from src.tools.consolidador.consolidador_v2 import Consolidador
        return Consolidador()

    def test_cached_similarity_returns_int(self):
        c = self._make_consolidador()
        result = c._cached_similarity("nome", "nome")
        assert isinstance(result, int)
        assert result == 100

    def test_cached_similarity_same_result_as_uncached(self):
        c = self._make_consolidador()
        result1 = c._cached_similarity("produto", "product")
        result2 = c._cached_similarity("produto", "product")
        assert result1 == result2

    def test_cached_similarity_cache_info(self):
        c = self._make_consolidador()
        c._cached_similarity("a", "b")
        c._cached_similarity("a", "b")
        c._cached_similarity("x", "y")
        info = c._cached_similarity.cache_info()
        assert info.hits >= 1
        assert info.misses >= 2

    def test_cached_similarity_case_insensitive(self):
        c = self._make_consolidador()
        result = c._cached_similarity("PRODUTO", "produto")
        assert result == 100


class TestConciliadorXmlErrors:
    """Testes de XML error tracking do Conciliador"""

    def _make_conciliador(self):
        from src.tools.conciliador.conciliador_v2 import Conciliador
        return Conciliador()

    def test_load_nfe_returns_dict_structure(self, tmp_path):
        c = self._make_conciliador()
        result = c._load_nfe_files(str(tmp_path))
        assert isinstance(result, dict)
        assert "data" in result
        assert "xml_errors" in result
        assert "total_files" in result
        assert "loaded" in result

    def test_load_nfe_empty_folder(self, tmp_path):
        c = self._make_conciliador()
        result = c._load_nfe_files(str(tmp_path))
        assert result["data"] == []
        assert result["xml_errors"] == []
        assert result["total_files"] == 0
        assert result["loaded"] == 0

    def test_load_nfe_valid_xml(self, tmp_path):
        c = self._make_conciliador()
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <nfeProc>
            <NFe>
                <infNFe>
                    <ide>
                        <nNF>123</nNF>
                        <serie>1</serie>
                        <dhEmi>2024-01-15</dhEmi>
                    </ide>
                    <total>
                        <ICMSTot>
                            <vNF>100.00</vNF>
                        </ICMSTot>
                    </total>
                    <dest>
                        <xNome>Cliente Teste</xNome>
                    </dest>
                </infNFe>
            </NFe>
        </nfeProc>"""
        xml_file = tmp_path / "nota1.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        result = c._load_nfe_files(str(tmp_path))
        assert result["loaded"] == 1
        assert result["total_files"] == 1
        assert len(result["xml_errors"]) == 0
        assert result["data"][0]["numero"] == "123"

    def test_load_nfe_invalid_xml_tracked(self, tmp_path):
        c = self._make_conciliador()
        xml_file = tmp_path / "bad.xml"
        xml_file.write_text("<invalid>not well formed</bad>", encoding="utf-8")
        
        result = c._load_nfe_files(str(tmp_path))
        assert result["loaded"] == 0
        assert len(result["xml_errors"]) == 1
        assert result["xml_errors"][0]["file"] == "bad.xml"
        assert "error" in result["xml_errors"][0]

    def test_load_nfe_mixed_valid_invalid(self, tmp_path):
        c = self._make_conciliador()
        
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <nfeProc>
            <NFe>
                <infNFe>
                    <ide><nNF>001</nNF><dhEmi>2024-01-01</dhEmi></ide>
                    <total><ICMSTot><vNF>50.00</vNF></ICMSTot></total>
                    <dest><xNome>CLI</xNome></dest>
                </infNFe>
            </NFe>
        </nfeProc>"""
        (tmp_path / "good.xml").write_text(valid_xml, encoding="utf-8")
        (tmp_path / "bad.xml").write_text("not xml at all", encoding="utf-8")
        
        result = c._load_nfe_files(str(tmp_path))
        assert result["loaded"] == 1
        assert result["total_files"] == 2
        assert len(result["xml_errors"]) == 1

    def test_progress_callback_called(self, tmp_path):
        c = self._make_conciliador()
        progress_mock = MagicMock()
        c.progress_callback = progress_mock
        
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <nfeProc>
            <NFe>
                <infNFe>
                    <ide><nNF>1</nNF><dhEmi>2024-01-01</dhEmi></ide>
                    <total><ICMSTot><vNF>10</vNF></ICMSTot></total>
                    <dest><xNome>X</xNome></dest>
                </infNFe>
            </NFe>
        </nfeProc>"""
        (tmp_path / "test.xml").write_text(valid_xml, encoding="utf-8")
        
        c._load_nfe_files(str(tmp_path))
        progress_mock.assert_called()


class TestConciliadorReconcileReturns:
    """Testes de retorno do reconcile_nfe incluindo xml_errors"""

    def test_reconcile_nfe_no_xml_returns_errors(self, tmp_path):
        from src.tools.conciliador.conciliador_v2 import Conciliador
        c = Conciliador()
        bank = tmp_path / "bank.csv"
        bank.write_text("data,valor,descricao\n2024-01-01,100,teste\n", encoding="utf-8")
        result = c.reconcile_nfe(str(tmp_path / "empty"), str(bank), str(tmp_path / "out.xlsx"))
        assert result["success"] is False
        assert "xml_errors" in result
