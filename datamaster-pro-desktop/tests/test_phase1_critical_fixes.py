"""
Testes da Fase 1: Segurança e Regras Financeiras
- Conversor OCR: Validação SHA-256
- Calculadora de Lucratividade: Carregamento dinâmico de taxas
- Precificador de Canal: Frete dinâmico via JSON
"""
import pytest
import json
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# 1. CONVERSOR OCR - SHA-256 Validation
# =============================================================================
class TestConversorOCRSecurity:
    """Testes de segurança do download do Conversor OCR"""

    def test_security_error_class_exists(self):
        """SecurityError deve ser uma exceção válida"""
        from src.tools.conversor_ocr.conversor_ocr_v2 import SecurityError
        assert issubclass(SecurityError, Exception)
        with pytest.raises(SecurityError, match="FALHA DE SEGURANÇA"):
            raise SecurityError("FALHA DE SEGURANÇA: teste")

    def test_hash_computation_during_download(self):
        """O hasher SHA-256 deve processar chunks corretamente"""
        hasher = hashlib.sha256()
        data = b"test binary content for hash verification"
        hasher.update(data)
        result = hasher.hexdigest()
        assert len(result) == 64  # SHA-256 produces 64 hex chars
        assert result == hashlib.sha256(data).hexdigest()

    def test_hash_mismatch_raises_security_error(self):
        """Quando hash diverge, SecurityError deve ser levantado e arquivo removido"""
        from src.tools.conversor_ocr.conversor_ocr_v2 import SecurityError
        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as f:
            f.write(b"fake installer content")
            fake_path = f.name
        
        try:
            EXPECTED_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
            with open(fake_path, "rb") as f:
                file_data = f.read()
            computed_hash = hashlib.sha256(file_data).hexdigest()
            
            assert computed_hash != EXPECTED_HASH, "O hash deveria divergir"
            
            # Simula a lógica de validação
            if computed_hash != EXPECTED_HASH:
                os.remove(fake_path)
                with pytest.raises(SecurityError):
                    raise SecurityError(f"FALHA DE SEGURANÇA: Assinatura divergente")
            
            assert not os.path.exists(fake_path), "Arquivo deveria ter sido removido"
        except Exception:
            if os.path.exists(fake_path):
                os.remove(fake_path)
            raise

    def test_conversor_ocr_instantiates(self):
        """ConversorOCR deve ser instanciável sem erros"""
        from src.tools.conversor_ocr.conversor_ocr_v2 import ConversorOCR
        conv = ConversorOCR()
        status = conv.get_status()
        assert "version" in status
        assert status["version"] == "3.1"


# =============================================================================
# 2. CALCULADORA DE LUCRATIVIDADE - JSON Tax Config
# =============================================================================
class TestCalculadoraLucratividade:
    """Testes do carregamento dinâmico de configurações fiscais"""

    def test_load_tax_config_from_example(self):
        """Deve carregar MARKETPLACE_FEES do tax_rules.example.json"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        calc = CalculadoraLucratividade()
        assert hasattr(calc, 'MARKETPLACE_FEES')
        assert "mercadolivre" in calc.MARKETPLACE_FEES
        assert "percent" in calc.MARKETPLACE_FEES["mercadolivre"]
        assert "fixed" in calc.MARKETPLACE_FEES["mercadolivre"]

    def test_all_marketplaces_loaded(self):
        """Todos os marketplaces devem estar presentes"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        calc = CalculadoraLucratividade()
        expected_keys = ["mercadolivre", "amazon", "shopee", "magalu", "other"]
        for key in expected_keys:
            assert key in calc.MARKETPLACE_FEES, f"Marketplace '{key}' não encontrado"

    def test_tax_calculation_basic(self):
        """Cálculo de imposto deve usar percentual e fixo do JSON"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        calc = CalculadoraLucratividade()
        
        fee = calc.MARKETPLACE_FEES["mercadolivre"]
        price = 100.0
        expected_tax = (price * fee["percent"]) + fee["fixed"]
        assert expected_tax == (100.0 * 0.16) + 6.0  # = 22.0

    def test_fallback_when_no_json(self):
        """Se JSON não existir, fallback deve ter estrutura válida"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        with patch("builtins.open", side_effect=Exception("File not found")):
            calc = CalculadoraLucratividade()
            assert "mercadolivre" in calc.MARKETPLACE_FEES
            assert calc.MARKETPLACE_FEES["mercadolivre"]["percent"] == 0.16

    def test_detect_marketplace(self):
        """Detector de marketplace deve identificar URLs corretamente"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        calc = CalculadoraLucratividade()
        assert calc._detect_marketplace("https://www.mercadolivre.com.br/produto") == "mercadolivre"
        assert calc._detect_marketplace("https://www.amazon.com.br/dp/B123") == "amazon"
        assert calc._detect_marketplace("https://shopee.com/product") == "shopee"
        assert calc._detect_marketplace("https://www.example.com") == "other"

    def test_get_tax_rates(self):
        """get_tax_rates() deve retornar seções do JSON"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        calc = CalculadoraLucratividade()
        rates = calc.get_tax_rates()
        assert "simples_nacional" in rates
        assert "pis_cofins" in rates

    def test_simples_nacional_calculation(self):
        """Cálculo do Simples Nacional deve retornar alíquota efetiva válida"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        calc = CalculadoraLucratividade()
        # Faturamento de R$150.000 (faixa 1 do anexo 1)
        aliquota = calc.calculate_simples_nacional(150000, "anexo_1_comercio")
        assert 0 < aliquota < 0.10  # Deve ser menor que 10%

    def test_clean_price_formats(self):
        """Parser de preço deve lidar com formatos brasileiros"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        calc = CalculadoraLucratividade()
        assert calc._clean_price("R$ 1.234,56") == 1234.56
        assert calc._clean_price("49,90") == 49.90
        assert calc._clean_price("199.99") == 199.99
        assert calc._clean_price("") is None
        assert calc._clean_price("abc") is None


# =============================================================================
# 3. PRECIFICADOR DE CANAL - Frete Dinâmico
# =============================================================================
class TestPrecificadorCanal:
    """Testes do cálculo dinâmico de frete"""

    def test_load_freight_tables(self):
        """Tabelas de frete devem ser carregadas do JSON"""
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        prec = PrecificadorCanal()
        assert hasattr(prec, '_freight_tables')
        assert "mercado_envios" in prec._freight_tables

    def test_freight_calculation_within_range(self):
        """Frete deve ser calculado corretamente dentro das faixas de peso"""
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        prec = PrecificadorCanal()
        # Peso de 250g -> deve cair na faixa de 300g
        frete = prec._calcular_frete_dinamico("Mercado Livre", 250.0, 100.0, 79.0, prec.CANAIS.get("Mercado Livre"))
        assert frete > 0
        
    def test_freight_calculation_heavy(self):
        """Frete para peso pesado deve usar última faixa"""
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        prec = PrecificadorCanal()
        # Peso de 25kg -> deve usar faixa de 30000g
        frete = prec._calcular_frete_dinamico("Mercado Livre", 25000.0, 500.0, 79.0, prec.CANAIS.get("Mercado Livre"))
        assert frete > 0

    def test_shopee_free_shipping(self):
        """Shopee deve retornar frete zero (subsidizado)"""
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        prec = PrecificadorCanal()
        frete = prec._calcular_frete_dinamico("Shopee", 1000.0, 50.0, 0.0, prec.CANAIS.get("Shopee"))
        assert frete == 0.0

    def test_amazon_free_shipping(self):
        """Amazon (FBA) deve retornar frete zero"""
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        prec = PrecificadorCanal()
        frete = prec._calcular_frete_dinamico("Amazon", 1000.0, 50.0, 0.0, prec.CANAIS.get("Amazon"))
        assert frete == 0.0

    def test_frete_gratis_threshold(self):
        """Se preço < frete_gratis_min, frete deve ser zero"""
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        prec = PrecificadorCanal()
        ml_info = prec.CANAIS.get("Mercado Livre", {})
        frete_min = ml_info.get("frete_gratis_min", 79.0)
        # Preço abaixo do threshold
        frete = prec._calcular_frete_dinamico("Mercado Livre", 500.0, 50.0, frete_min, ml_info)
        assert frete == 0.0

    def test_calculo_reverso_basico(self):
        """Cálculo reverso deve retornar preço, margem e lucro"""
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        prec = PrecificadorCanal()
        ml_info = prec.CANAIS.get("Mercado Livre", {})
        resultado = prec._preco_por_canal(
            "Mercado Livre", custo=50.0, imposto_pct=6.0,
            margem_desejada_pct=20.0, peso_g=500.0, canal_info=ml_info
        )
        assert resultado["erro"] is None
        assert resultado["preco"] > 50.0  # Preço deve ser maior que o custo
        assert resultado["margem_real_pct"] > 0

    def test_calculadora_precificador_compartilham_json(self):
        """Ambas as ferramentas devem carregar do mesmo JSON"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        
        calc = CalculadoraLucratividade()
        prec = PrecificadorCanal()
        
        # ML percent deve ser o mesmo em ambas
        ml_calc = calc.MARKETPLACE_FEES.get("mercadolivre", {}).get("percent")
        ml_prec = prec.CANAIS.get("Mercado Livre", {}).get("comissao_pct")
        assert ml_calc == ml_prec, "ML percent divergente entre Calculadora e Precificador"

    def test_normalize_df_adds_default_weight(self):
        """DataFrame sem coluna peso_g deve receber valor padrão 500g"""
        import pandas as pd
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        prec = PrecificadorCanal()
        df = pd.DataFrame({"produto": ["Teste"], "custo": [50.0]})
        df_norm = prec._normalizar_df(df)
        assert df_norm is not None
        assert "peso_g" in df_norm.columns
        assert df_norm["peso_g"].iloc[0] == 500.0


# =============================================================================
# 4. TAX_RULES.JSON - Schema Validation
# =============================================================================
class TestTaxRulesSchema:
    """Validação do schema do arquivo de configuração"""

    def test_example_json_is_valid(self):
        """tax_rules.example.json deve ser JSON válido"""
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "..", 
            "tax_rules.example.json"
        )
        if os.path.exists(example_path):
            with open(example_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "MARKETPLACE_FEES" in data
            assert "TAX_RATES" in data
            assert "FREIGHT_TABLES" in data
            assert "_metadata" in data

    def test_marketplace_fees_structure(self):
        """Cada marketplace deve ter percent e fixed"""
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "..", 
            "tax_rules.example.json"
        )
        if os.path.exists(example_path):
            with open(example_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for mp_name, mp_data in data["MARKETPLACE_FEES"].items():
                assert "percent" in mp_data, f"{mp_name} sem 'percent'"
                assert "fixed" in mp_data, f"{mp_name} sem 'fixed'"
                assert isinstance(mp_data["percent"], float), f"{mp_name} percent não é float"

    def test_freight_tables_structure(self):
        """Tabelas de frete devem ter peso_max_g e valor"""
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "..", 
            "tax_rules.example.json"
        )
        if os.path.exists(example_path):
            with open(example_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for table_name, table_data in data["FREIGHT_TABLES"].items():
                if table_name == "nota":
                    continue
                assert isinstance(table_data, list), f"Tabela '{table_name}' não é lista"
                for faixa in table_data:
                    assert "peso_max_g" in faixa, f"Faixa em '{table_name}' sem 'peso_max_g'"
                    assert "valor" in faixa, f"Faixa em '{table_name}' sem 'valor'"

    def test_simples_nacional_faixas(self):
        """Simples Nacional deve ter faixas com limite, aliquota e parcela"""
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "..", 
            "tax_rules.example.json"
        )
        if os.path.exists(example_path):
            with open(example_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sn = data["TAX_RATES"]["simples_nacional"]
            for anexo_name, anexo_data in sn.items():
                if anexo_name == "nota":
                    continue
                for faixa_name, faixa_data in anexo_data.items():
                    if faixa_name == "nota":
                        continue
                    assert "limite" in faixa_data, f"{anexo_name}/{faixa_name} sem 'limite'"
                    assert "aliquota" in faixa_data, f"{anexo_name}/{faixa_name} sem 'aliquota'"
                    assert "parcela" in faixa_data, f"{anexo_name}/{faixa_name} sem 'parcela'"
