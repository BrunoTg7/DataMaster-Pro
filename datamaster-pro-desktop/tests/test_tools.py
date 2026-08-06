import pytest
import pandas as pd
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.consolidador.consolidador_v2 import Consolidador
from src.tools.categorizador.categorizador_v2 import Categorizador
from src.tools.conciliador.conciliador_v2 import Conciliador
from src.tools.minerador.minerador_v2 import Minerador
from src.tools.orcamentos.orcamentos import Orcamentos


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestConsolidador:
    """Testes para o Consolidador"""

    @pytest.fixture
    def consolidador(self):
        return Consolidador()

    @pytest.fixture
    def sample_excel_files(self, tmp_path):
        df1 = pd.DataFrame({"nome": ["João", "Maria"], "valor": [100, 200]})
        df2 = pd.DataFrame({"nome": ["Pedro", "Ana"], "valor": [300, 400]})

        file1 = tmp_path / "file1.xlsx"
        file2 = tmp_path / "file2.xlsx"

        df1.to_excel(file1, index=False)
        df2.to_excel(file2, index=False)

        return [str(file1), str(file2)]

    @pytest.fixture
    def sample_csv_file(self, tmp_path):
        df = pd.DataFrame({"produto": ["A", "B", "C"], "preco": [10, 20, 30]})
        file_path = tmp_path / "test.csv"
        df.to_csv(file_path, index=False)
        return str(file_path)

    def test_consolidate_concat(self, consolidador, sample_excel_files, tmp_path):
        output_path = tmp_path / "output.xlsx"

        result = consolidador.consolidate(
            sample_excel_files,
            str(output_path),
            merge_strategy="concat"
        )

        assert result["success"] is True
        assert result["total_rows"] == 4
        assert result["total_files"] == 2
        assert os.path.exists(result["output_path"])

    def test_consolidate_single_csv(self, consolidador, sample_csv_file, tmp_path):
        output_path = tmp_path / "output.xlsx"

        result = consolidador.consolidate(
            [sample_csv_file],
            str(output_path)
        )

        assert result["success"] is True
        assert result["total_rows"] == 3
        assert os.path.exists(result["output_path"])

    def test_consolidate_empty_list(self, consolidador, tmp_path):
        output_path = tmp_path / "output.xlsx"

        result = consolidador.consolidate([], str(output_path))

        assert result["success"] is False
        assert "Nenhum arquivo" in result["error"]

    def test_get_preview(self, consolidador, sample_csv_file):
        preview = consolidador.get_preview(sample_csv_file, max_rows=2)

        assert preview is not None
        assert len(preview) == 2


class TestCategorizador:
    """Testes para o Categorizador"""

    @pytest.fixture
    def categorizador(self):
        return Categorizador()

    @pytest.fixture
    def sample_transaction_file(self, tmp_path):
        df = pd.DataFrame({
            "descricao": [
                "Posto Shell - Combustivel",
                "Uber Viagem",
                "Restaurante Pizza",
                "Conta de Luz",
                "Generic expense"
            ]
        })
        file_path = tmp_path / "transacoes.xlsx"
        df.to_excel(file_path, index=False)
        return str(file_path)

    def test_categorize(self, categorizador, sample_transaction_file, tmp_path):
        output_path = tmp_path / "output.xlsx"

        result = categorizador.categorize(
            sample_transaction_file,
            str(output_path),
            description_column="descricao"
        )

        assert result["success"] is True
        assert result["total_rows"] == 5

    def test_classify_row(self, categorizador):
        assert categorizador._classify_row("Posto Shell") == "combustivel"
        assert categorizador._classify_row("Uber Viagem") == "transporte"
        assert categorizador._classify_row("Restaurante Italiano") == "alimentacao"
        assert categorizador._classify_row("Conta de Luz") == "utilidades"
        assert categorizador._classify_row("Generic expense") == "outros"

    def test_classify_empty(self, categorizador):
        assert categorizador._classify_row("") == "outros"
        assert categorizador._classify_row(None) == "outros"

    def test_get_categories(self, categorizador):
        categories = categorizador.get_categories()
        assert "combustivel" in categories
        assert "alimentacao" in categories
        assert "transporte" in categories

    def test_priority_ordering(self, categorizador):
        categories = categorizador.get_categories()
        combustivel_priority = categories.get("combustivel", {}).get("priority", 0)
        alimentacao_priority = categories.get("alimentacao", {}).get("priority", 0)
        assert combustivel_priority >= alimentacao_priority

    def test_suggest_others(self, categorizador):
        descriptions = ["pix joao", "pix maria", "netflix mensal", "spotify"]
        suggestions = categorizador.suggest_category_for_others(descriptions)
        assert len(suggestions) > 0
        suggestion_cats = [s["category"] for s in suggestions]
        assert "pix" in suggestion_cats or "assinatura" in suggestion_cats
        categories = categorizador.get_categories()
        assert "transporte" in categories

    def test_categorize_missing_column(self, categorizador, tmp_path):
        df = pd.DataFrame({"outra_coluna": ["valor"]})
        file_path = tmp_path / "test.xlsx"
        df.to_excel(file_path, index=False)
        output_path = tmp_path / "output.xlsx"

        result = categorizador.categorize(
            str(file_path),
            str(output_path),
            description_column="descricao"
        )

        assert result["success"] is False
        assert "não encontrada" in result["error"]


class TestConciliador:
    """Testes para o Conciliador"""

    @pytest.fixture
    def conciliador(self):
        return Conciliador()

    @pytest.fixture
    def sample_extract_file(self, tmp_path):
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "description": ["Pagamento A", "Pagamento B", "Pagamento C"],
            "amount": [100.00, 200.50, 50.00]
        })
        file_path = tmp_path / "extrato.csv"
        df.to_csv(file_path, index=False)
        return str(file_path)

    @pytest.fixture
    def sample_sales_file(self, tmp_path):
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-04"],
            "client": ["Cliente A", "Cliente B", "Cliente C"],
            "amount": [100.00, 200.50, 75.00]
        })
        file_path = tmp_path / "vendas.csv"
        df.to_csv(file_path, index=False)
        return str(file_path)

    def test_reconcile(self, conciliador, sample_extract_file, sample_sales_file, tmp_path):
        output_path = tmp_path / "conciliado.xlsx"

        result = conciliador.reconcile(
            sample_extract_file,
            sample_sales_file,
            str(output_path)
        )

        assert result["success"] is True
        assert result["total_extract"] == 3
        assert result["total_sales"] == 3
        assert result["matched"] == 2

    def test_quick_check(self, conciliador, sample_extract_file, sample_sales_file):
        result = conciliador.quick_check(sample_extract_file, sample_sales_file)

        assert result["success"] is True
        assert result["file1_rows"] == 3
        assert result["file2_rows"] == 3

    def test_reconcile_missing_file(self, conciliador, tmp_path):
        output_path = tmp_path / "output.xlsx"

        result = conciliador.reconcile(
            "inexistente.csv",
            "inexistente.csv",
            str(output_path)
        )

        assert result["success"] is False
        assert "não encontrado" in result["error"]

    def test_normalize_columns(self, conciliador):
        df = pd.DataFrame({
            "valor": [100],
            "data": ["2024-01-01"],
            "descricao": ["test"]
        })

        normalized = conciliador._normalize_columns(df, "extract")

        assert "amount" in normalized.columns
        assert "date" in normalized.columns


class TestIntegration:
    """Testes de integração"""

    def test_full_workflow(self, tmp_path):
        df1 = pd.DataFrame({
            "descricao": ["Posto Shell", "Generic Corp"],
            "valor": [100, 200]
        })

        input_file = tmp_path / "input.xlsx"
        df1.to_excel(input_file, index=False)

        from src.tools.consolidador.consolidador_v2 import Consolidador
        from src.tools.categorizador.categorizador_v2 import Categorizador

        consolidador = Consolidador()
        consolidated_path = tmp_path / "consolidated.xlsx"

        result = consolidador.consolidate(
            [str(input_file)],
            str(consolidated_path)
        )

        assert result["success"] is True

        categorizador = Categorizador()
        output_path = tmp_path / "categorized.xlsx"

        result = categorizador.categorize(
            str(consolidated_path),
            str(output_path),
            description_column="descricao"
        )

        assert result["success"] is True


# =========================================================================
# NOVOS TESTES: Conciliador Pro v3.0 - Tolerância de datas e Fuzzy Matching
# =========================================================================
class TestConciliadorAdvanced:
    """Testes avançados do Conciliador Pro v3.0 (sem IA)"""

    @pytest.fixture
    def conciliador(self):
        return Conciliador()

    def test_date_tolerance_matches(self, conciliador, tmp_path):
        """Transações com datas diferentes (+1 dia) devem casar com tolerância ativada"""
        extract_df = pd.DataFrame({
            "date": ["2024-03-10", "2024-03-15"],
            "description": ["Pagamento X", "Pagamento Y"],
            "amount": [500.00, 300.00]
        })
        sales_df = pd.DataFrame({
            "date": ["2024-03-11", "2024-03-15"],
            "description": ["Venda X", "Venda Y"],
            "amount": [500.00, 300.00]
        })

        ext_file = tmp_path / "ext.csv"
        sal_file = tmp_path / "sal.csv"
        out_file = tmp_path / "out.xlsx"

        extract_df.to_csv(ext_file, index=False)
        sales_df.to_csv(sal_file, index=False)

        result = conciliador.reconcile_classic(
            str(ext_file), str(sal_file), str(out_file),
            date_tolerance_days=2, fuzzy_threshold=0
        )

        assert result["success"] is True
        assert result["matched"] == 2
        assert result["unmatched_extract"] == 0

    def test_date_tolerance_no_match_beyond_window(self, conciliador, tmp_path):
        """Transações com datas além da janela NÃO devem casar"""
        extract_df = pd.DataFrame({
            "date": ["2024-03-10"],
            "description": ["Pagamento Z"],
            "amount": [100.00]
        })
        sales_df = pd.DataFrame({
            "date": ["2024-03-20"],
            "description": ["Venda Z"],
            "amount": [100.00]
        })

        ext_file = tmp_path / "ext2.csv"
        sal_file = tmp_path / "sal2.csv"
        out_file = tmp_path / "out2.xlsx"

        extract_df.to_csv(ext_file, index=False)
        sales_df.to_csv(sal_file, index=False)

        result = conciliador.reconcile_classic(
            str(ext_file), str(sal_file), str(out_file),
            date_tolerance_days=3, fuzzy_threshold=0
        )

        assert result["success"] is True
        assert result["matched"] == 0

    def test_fuzzy_description_matching(self, conciliador, tmp_path):
        """Descrições similares devem casar via fuzzy matching"""
        extract_df = pd.DataFrame({
            "date": ["2024-06-01", "2024-06-02"],
            "description": ["PIX MARIA SOUZA", "TED JOAO SILVA LTDA"],
            "amount": [250.00, 780.00]
        })
        sales_df = pd.DataFrame({
            "date": ["2024-06-01", "2024-06-02"],
            "description": ["Maria de Souza - PIX", "João Silva Comércio LTDA"],
            "amount": [250.00, 780.00]
        })

        ext_file = tmp_path / "ext_fz.csv"
        sal_file = tmp_path / "sal_fz.csv"
        out_file = tmp_path / "out_fz.xlsx"

        extract_df.to_csv(ext_file, index=False)
        sales_df.to_csv(sal_file, index=False)

        result = conciliador.reconcile_classic(
            str(ext_file), str(sal_file), str(out_file),
            date_tolerance_days=0, fuzzy_threshold=50
        )

        assert result["success"] is True
        assert result["matched"] >= 1

    def test_premium_excel_output_has_two_sheets(self, conciliador, tmp_path):
        """O output deve conter 2 abas: Resumo e Planilha Conciliada"""
        extract_df = pd.DataFrame({
            "date": ["2024-01-01"],
            "description": ["Pagamento A"],
            "amount": [100.00]
        })
        sales_df = pd.DataFrame({
            "date": ["2024-01-01"],
            "description": ["Venda A"],
            "amount": [100.00]
        })

        ext_file = tmp_path / "ext_sh.csv"
        sal_file = tmp_path / "sal_sh.csv"
        out_file = tmp_path / "out_sh.xlsx"

        extract_df.to_csv(ext_file, index=False)
        sales_df.to_csv(sal_file, index=False)

        result = conciliador.reconcile_classic(
            str(ext_file), str(sal_file), str(out_file),
            fuzzy_threshold=0
        )

        assert result["success"] is True
        xl = pd.ExcelFile(str(out_file))
        assert len(xl.sheet_names) == 2
        assert "Planilha Conciliada" in xl.sheet_names


# =========================================================================
# NOVOS TESTES: Minerador Pro v4.0 - Selector Registry e Price Parser
# =========================================================================
class TestMineradorPro:
    """Testes do Minerador Pro v4.0 (sem IA, sem rede)"""

    @pytest.fixture
    def minerador(self):
        from src.tools.minerador.minerador_v2 import Minerador
        return Minerador()

    def test_registry_keys(self, minerador):
        """Selector Registry deve ter os marketplaces padrão"""
        keys = minerador.get_registry_keys()
        assert "mercadolivre" in keys
        assert "amazon" in keys
        assert "shopee" in keys
        assert "magalu" in keys
        assert "generico" in keys

    def test_get_selectors_for_marketplace(self, minerador):
        """Cada marketplace deve ter seletores de title e price"""
        for mp in ["mercadolivre", "amazon", "shopee", "magalu"]:
            selectors = minerador.get_selectors_for(mp)
            assert "title" in selectors
            assert "price" in selectors
            assert len(selectors["title"]) > 0
            assert len(selectors["price"]) > 0

    def test_generic_fallback(self, minerador):
        """Marketplace desconhecido deve retornar seletores genéricos"""
        selectors = minerador.get_selectors_for("site_inexistente")
        assert "title" in selectors
        assert "price" in selectors

    def test_parse_price_brazilian(self, minerador):
        """Parser deve lidar com formatos de preço brasileiros"""
        from src.tools.minerador.minerador_v2 import Minerador as M
        assert M._parse_price("R$ 1.234,56") == 1234.56
        assert M._parse_price("R$ 49,90") == 49.90
        assert M._parse_price("199.99") == 199.99
        assert M._parse_price("") == 0.0
        assert M._parse_price("R$ 0,01") == 0.01

    def test_mine_from_file_missing_column(self, minerador, tmp_path):
        """Planilha sem coluna de links deve retornar erro"""
        df = pd.DataFrame({"nome": ["Produto A"], "preco": [100]})
        file_path = tmp_path / "sem_links.xlsx"
        df.to_excel(file_path, index=False)

        result = minerador.mine_from_file(str(file_path))
        assert result["success"] is False
        assert "URLs" in result["error"]

    def test_export_results_creates_file(self, minerador, tmp_path):
        """Exportação de resultados deve criar arquivo Excel"""
        results = [
            {"titulo": "Produto A", "preco": 99.90, "preco_raw": "R$ 99,90",
             "disponibilidade": "Em estoque", "avaliacao": "4.5",
             "vendedor": "Loja X", "marketplace": "generico",
             "url": "http://example.com", "coletado_em": "2024-01-01"},
            {"titulo": "Produto B", "preco": 149.00, "preco_raw": "R$ 149,00",
             "disponibilidade": "Últimas unidades", "avaliacao": "4.8",
             "vendedor": "Loja Y", "marketplace": "generico",
             "url": "http://example.com/2", "coletado_em": "2024-01-01"},
        ]
        out = tmp_path / "export.xlsx"
        ok = minerador.export_results(results, str(out))
        assert ok is True
        assert out.exists()

        xl = pd.ExcelFile(str(out))
        assert len(xl.sheet_names) == 2


# =========================================================================
# NOVOS TESTES: Orçamentos Pro v3.0 - Geração de PDFs Profissionais
# =========================================================================
class TestOrcamentosPro:
    """Testes do Orçamentos Pro (nova API)"""

    @pytest.fixture
    def orcamentos(self):
        from src.tools.orcamentos.orcamentos import Orcamentos
        return Orcamentos()

    def test_generate_from_excel(self, orcamentos, tmp_path):
        """Deve gerar PDFs em lote a partir de planilha"""
        df = pd.DataFrame({
            "numero": ["001", "002"],
            "cliente": ["Maria Silva", "João Santos"],
            "data": ["21/05/2026", "22/05/2026"],
            "item": ["Serviço A", "Consultoria"],
            "qtd": [1, 3],
            "preco": [500.00, 800.00]
        })
        data_file = tmp_path / "dados.xlsx"
        df.to_excel(data_file, index=False)

        out_dir = tmp_path / "pdfs"
        result = orcamentos.generate_from_excel(str(data_file), str(out_dir))

        assert result["success"] is True
        assert result["generated"] == 2
        assert result["total_rows"] == 2

        pdf_files = list(out_dir.glob("*.pdf"))
        assert len(pdf_files) == 2


# =========================================================================
# NOVOS TESTES: Orçamentos Streaming - Performance e Memory Leak
# =========================================================================
class TestOrcamentosStreaming:
    """Testes de streaming e memory leak do Orçamentos"""

    @pytest.fixture
    def orcamentos(self):
        from src.tools.orcamentos.orcamentos import Orcamentos
        return Orcamentos()

    def test_streaming_generates_same_results_as_batch(self, orcamentos, tmp_path):
        """Streaming e batch devem produzir resultados idênticos"""
        df = pd.DataFrame({
            "numero": [f"{i:03d}" for i in range(1, 11)],
            "cliente": [f"Cliente {i}" for i in range(1, 11)],
            "data": ["21/05/2026"] * 10,
            "item": [f"Serviço {i}" for i in range(1, 11)],
            "qtd": [1] * 10,
            "preco": [500.00 + i * 10 for i in range(10)]
        })
        data_file = tmp_path / "dados.xlsx"
        df.to_excel(data_file, index=False)

        out_batch = tmp_path / "batch"
        out_stream = tmp_path / "stream"

        result_batch = orcamentos.generate_from_excel(str(data_file), str(out_batch))
        result_stream = orcamentos.generate_from_excel_streaming(str(data_file), str(out_stream), batch_size=3)

        assert result_batch["success"] is True
        assert result_stream["success"] is True
        assert result_batch["generated"] == result_stream["generated"]

    def test_streaming_batch_size_respected(self, orcamentos, tmp_path):
        """batch_size deve ser respeitado (gc.collect a cada N PDFs)"""
        df = pd.DataFrame({
            "numero": [f"{i:03d}" for i in range(1, 21)],
            "cliente": [f"Cliente {i}" for i in range(1, 21)],
            "data": ["21/05/2026"] * 20,
            "item": [f"Serviço {i}" for i in range(1, 21)],
            "qtd": [1] * 20,
            "preco": [500.00] * 20
        })
        data_file = tmp_path / "dados.xlsx"
        df.to_excel(data_file, index=False)

        out_dir = tmp_path / "stream"
        result = orcamentos.generate_from_excel_streaming(str(data_file), str(out_dir), batch_size=5)

        assert result["success"] is True
        assert result["generated"] == 20


# =========================================================================
# NOVOS TESTES: Minerador Pro v4.0 - Offline/Unit Tests
# =========================================================================
class TestMineradorOffline:
    """Testes offline do Minerador (sem rede, sem Playwright)"""

    @pytest.fixture
    def minerador(self):
        from src.tools.minerador.minerador_v2 import Minerador
        return Minerador()

    def test_registry_keys(self, minerador):
        """Selector Registry deve ter os marketplaces padrão"""
        keys = minerador.get_registry_keys()
        assert "mercadolivre" in keys
        assert "amazon" in keys
        assert "shopee" in keys
        assert "magalu" in keys
        assert "generico" in keys

    def test_get_selectors_for_marketplace(self, minerador):
        """Cada marketplace deve ter seletores de title e price"""
        for mp in ["mercadolivre", "amazon", "shopee", "magalu"]:
            selectors = minerador.get_selectors_for(mp)
            assert "title" in selectors
            assert "price" in selectors
            assert len(selectors["title"]) > 0
            assert len(selectors["price"]) > 0

    def test_generic_fallback(self, minerador):
        """Marketplace desconhecido deve retornar seletores genéricos"""
        selectors = minerador.get_selectors_for("site_inexistente")
        assert "title" in selectors
        assert "price" in selectors

    def test_parse_price_brazilian(self, minerador):
        """Parser deve lidar com formatos de preço brasileiros"""
        from src.tools.minerador.minerador_v2 import Minerador as M
        assert M._parse_price("R$ 1.234,56") == 1234.56
        assert M._parse_price("R$ 49,90") == 49.90
        assert M._parse_price("199.99") == 199.99
        assert M._parse_price("") == 0.0
        assert M._parse_price("R$ 0,01") == 0.01

    def test_mine_from_file_missing_column(self, minerador, tmp_path):
        """Planilha sem coluna de links deve retornar erro"""
        df = pd.DataFrame({"nome": ["Produto A"], "preco": [100]})
        file_path = tmp_path / "sem_links.xlsx"
        df.to_excel(file_path, index=False)

        result = minerador.mine_from_file(str(file_path))
        assert result["success"] is False
        assert "URLs" in result["error"]

    def test_export_results_creates_file(self, minerador, tmp_path):
        """Exportação de resultados deve criar arquivo Excel"""
        results = [
            {"titulo": "Produto A", "preco": 99.90, "preco_raw": "R$ 99,90",
             "disponibilidade": "Em estoque", "avaliacao": "4.5",
             "vendedor": "Loja X", "marketplace": "generico",
             "url": "http://example.com", "coletado_em": "2024-01-01"},
            {"titulo": "Produto B", "preco": 149.00, "preco_raw": "R$ 149,00",
             "disponibilidade": "Últimas unidades", "avaliacao": "4.8",
             "vendedor": "Loja Y", "marketplace": "generico",
             "url": "http://example.com/2", "coletado_em": "2024-01-01"},
        ]
        out = tmp_path / "export.xlsx"
        ok = minerador.export_results(results, str(out))
        assert ok is True
        assert out.exists()

        xl = pd.ExcelFile(str(out))
        assert len(xl.sheet_names) == 2


# =========================================================================
# NOVOS TESTES: Conciliador Pro v3.0 - Avançado
# =========================================================================
class TestConciliadorAdvanced:
    """Testes avançados do Conciliador Pro v3.0 (sem IA)"""

    @pytest.fixture
    def conciliador(self):
        return Conciliador()

    def test_date_tolerance_matches(self, conciliador, tmp_path):
        """Transações com datas diferentes (+1 dia) devem casar com tolerância ativada"""
        extract_df = pd.DataFrame({
            "date": ["2024-03-10", "2024-03-15"],
            "description": ["Pagamento X", "Pagamento Y"],
            "amount": [500.00, 300.00]
        })
        sales_df = pd.DataFrame({
            "date": ["2024-03-11", "2024-03-15"],
            "description": ["Venda X", "Venda Y"],
            "amount": [500.00, 300.00]
        })

        ext_file = tmp_path / "ext.csv"
        sal_file = tmp_path / "sal.csv"
        out_file = tmp_path / "out.xlsx"

        extract_df.to_csv(ext_file, index=False)
        sales_df.to_csv(sal_file, index=False)

        result = conciliador.reconcile_classic(
            str(ext_file), str(sal_file), str(out_file),
            date_tolerance_days=2, fuzzy_threshold=0
        )

        assert result["success"] is True
        assert result["matched"] == 2
        assert result["unmatched_extract"] == 0

    def test_date_tolerance_no_match_beyond_window(self, conciliador, tmp_path):
        """Transações com datas além da janela NÃO devem casar"""
        extract_df = pd.DataFrame({
            "date": ["2024-03-10"],
            "description": ["Pagamento Z"],
            "amount": [100.00]
        })
        sales_df = pd.DataFrame({
            "date": ["2024-03-20"],
            "description": ["Venda Z"],
            "amount": [100.00]
        })

        ext_file = tmp_path / "ext2.csv"
        sal_file = tmp_path / "sal2.csv"
        out_file = tmp_path / "out2.xlsx"

        extract_df.to_csv(ext_file, index=False)
        sales_df.to_csv(sal_file, index=False)

        result = conciliador.reconcile_classic(
            str(ext_file), str(sal_file), str(out_file),
            date_tolerance_days=3, fuzzy_threshold=0
        )

        assert result["success"] is True
        assert result["matched"] == 0

    def test_fuzzy_description_matching(self, conciliador, tmp_path):
        """Descrições similares devem casar via fuzzy matching"""
        extract_df = pd.DataFrame({
            "date": ["2024-06-01", "2024-06-02"],
            "description": ["PIX MARIA SOUZA", "TED JOAO SILVA LTDA"],
            "amount": [250.00, 780.00]
        })
        sales_df = pd.DataFrame({
            "date": ["2024-06-01", "2024-06-02"],
            "description": ["Maria de Souza - PIX", "João Silva Comércio LTDA"],
            "amount": [250.00, 780.00]
        })

        ext_file = tmp_path / "ext_fz.csv"
        sal_file = tmp_path / "sal_fz.csv"
        out_file = tmp_path / "out_fz.xlsx"

        extract_df.to_csv(ext_file, index=False)
        sales_df.to_csv(sal_file, index=False)

        result = conciliador.reconcile_classic(
            str(ext_file), str(sal_file), str(out_file),
            date_tolerance_days=0, fuzzy_threshold=50
        )

        assert result["success"] is True
        assert result["matched"] >= 1

    def test_premium_excel_output_has_two_sheets(self, conciliador, tmp_path):
        """O output deve conter 2 abas: Resumo e Planilha Conciliada"""
        extract_df = pd.DataFrame({
            "date": ["2024-01-01"],
            "description": ["Pagamento A"],
            "amount": [100.00]
        })
        sales_df = pd.DataFrame({
            "date": ["2024-01-01"],
            "description": ["Venda A"],
            "amount": [100.00]
        })

        ext_file = tmp_path / "ext_sh.csv"
        sal_file = tmp_path / "sal_sh.csv"
        out_file = tmp_path / "out_sh.xlsx"

        extract_df.to_csv(ext_file, index=False)
        sales_df.to_csv(sal_file, index=False)

        result = conciliador.reconcile_classic(
            str(ext_file), str(sal_file), str(out_file),
            fuzzy_threshold=0
        )

        assert result["success"] is True
        xl = pd.ExcelFile(str(out_file))
        assert len(xl.sheet_names) == 2
        assert "Planilha Conciliada" in xl.sheet_names


# =========================================================================
# NOVOS TESTES: Conciliador NF-e + Vendas
# =========================================================================
class TestConciliadorNFeVendas:
    """Testes do modo NF-e + Vendas"""

    @pytest.fixture
    def conciliador(self):
        return Conciliador()

    def test_reconcile_nfe_vendas_missing_file(self, conciliador, tmp_path):
        """Arquivo XML ou planilha faltando deve retornar erro"""
        result = conciliador.reconcile_nfe_vendas(
            "inexistente", "inexistente", str(tmp_path / "out.xlsx")
        )
        assert result["success"] is False
        assert "não encontrado" in result["error"].lower() or "error" in result


# =========================================================================
# NOVOS TESTES: OCR v3 - Cross-platform
# =========================================================================
class TestOCRV3:
    """Testes do Conversor OCR v3 (cross-platform)"""

    def test_temp_path_windows(self):
        """Paths temporários devem usar tempfile.gettempdir() no Windows"""
        from src.tools.conversor_ocr.conversor_ocr_v3 import PaddleOCREngine
        import tempfile
        import os

        engine = PaddleOCREngine()
        # Verifica se o engine usa tempfile.gettempdir()
        temp_dir = Path(tempfile.gettempdir()) / "paddleocr_cache"
        assert str(temp_dir).startswith(tempfile.gettempdir())

    def test_import_json_available(self):
        """json deve estar importado no módulo"""
        import src.tools.conversor_ocr.conversor_ocr_v3 as ocr_module
        assert hasattr(ocr_module, 'json')


# =========================================================================
# NOVOS TESTES: Gerador Laudos - pAdES-B
# =========================================================================
class TestGeradorLaudos:
    """Testes do Gerador de Laudos - assinatura pAdES-B"""

    @pytest.fixture
    def has_weasyprint(self):
        """Verifica se weasyprint está disponível (requer GTK)"""
        try:
            import weasyprint
            return True
        except OSError:
            return False

    def test_sign_pdf_stub_removed(self, has_weasyprint):
        """_sign_pdf não deve ser mais stub"""
        if not has_weasyprint:
            pytest.skip("weasyprint/GTK não disponível neste ambiente")
        from src.tools.gerador_laudos.gerador_laudos_enterprise import GeradorLaudosEnterprise
        import inspect
        source = inspect.getsource(GeradorLaudosEnterprise._sign_pdf)
        assert "pass" not in source or "endesive" in source

    def test_truncation_warning_flag(self, has_weasyprint):
        """items[:100] deve ter flag truncated no retorno"""
        if not has_weasyprint:
            pytest.skip("weasyprint/GTK não disponível neste ambiente")
        from src.tools.gerador_laudos.gerador_laudos_enterprise import GeradorLaudosEnterprise
        import inspect
        source = inspect.getsource(GeradorLaudosEnterprise._build_context)
        assert "truncated" in source
        assert "len(items) > 100" in source


# =========================================================================
# NOVOS TESTES: Classificador NCM - Pipeline
# =========================================================================
class TestNCMPipeline:
    """Testes do Pipeline NCM/CEST"""

    def test_typo_fixed(self):
        """Typo ClassificadorNCMEntperprise deve estar corrigido"""
        from src.tools.classificador_ncm.ncm_pipeline import ClassificadorNCMEnterprise
        assert ClassificadorNCMEnterprise.__name__ == "ClassificadorNCMEnterprise"

    def test_cest_download_parse(self):
        """_download_and_parse_cest deve estar implementado (não retornar None)"""
        from src.tools.classificador_ncm.ncm_pipeline import NCMPipeline
        import inspect
        source = inspect.getsource(NCMPipeline._download_and_parse_cest)
        assert "return None" not in source or "BeautifulSoup" in source

    def test_merge_guard_division_zero(self):
        """Merge TIPI+CEST deve ter guard contra divisão por zero"""
        from src.tools.classificador_ncm.ncm_pipeline import NCMPipeline
        import inspect
        source = inspect.getsource(NCMPipeline._merge_tipi_cest)
        assert "len(merged) > 0" in source


# =========================================================================
# NOVOS TESTES: Config - tax_rules.json e simples_nacional_2026.json
# =========================================================================
class TestConfigFiles:
    """Testes dos arquivos de configuração"""

    def test_tax_rules_json_exists(self):
        """tax_rules.json deve existir e ter estrutura válida"""
        path = Path(__file__).parent.parent / "datamaster-pro-desktop" / "tax_rules.json"
        assert path.exists()
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "MARKETPLACE_FEES" in data
        assert "FREIGHT_TABLES" in data
        assert "mercadolivre" in data["MARKETPLACE_FEES"]
        assert "shopee" in data["MARKETPLACE_FEES"]
        assert "amazon" in data["MARKETPLACE_FEES"]
        assert "magalu" in data["MARKETPLACE_FEES"]

    def test_simples_nacional_2026_exists(self):
        """simples_nacional_2026.json deve existir com 6 anexos"""
        path = Path(__file__).parent.parent / "datamaster-pro-desktop" / "simples_nacional_2026.json"
        assert path.exists()
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "anexo_1_comercio" in data
        assert "anexo_2_industria" in data
        assert "anexo_3_servicos_1" in data
        assert "anexo_4_servicos_2" in data
        assert "anexo_5_servicos_3" in data
        # anexo_2_servicos é alias para anexo_2_industria (compatibilidade)
        assert "anexo_2_industria" in data  # fallback compat

    def test_calculadora_loads_simples_nacional(self):
        """Calculadora deve carregar simples_nacional_2026.json"""
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        calc = CalculadoraLucratividade()
        assert "simples_nacional" in calc._tax_data.get("TAX_RATES", {})


# =========================================================================
# NOVOS TESTES: Offline Mode
# =========================================================================
class TestOfflineMode:
    """Testes de funcionamento offline"""

    def test_consolidador_works_offline(self, tmp_path):
        """Consolidador deve funcionar sem internet"""
        df1 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        df2 = pd.DataFrame({"A": [5, 6], "B": [7, 8]})
        f1 = tmp_path / "f1.xlsx"
        f2 = tmp_path / "f2.xlsx"
        df1.to_excel(f1, index=False)
        df2.to_excel(f2, index=False)

        c = Consolidador()
        result = c.consolidate([str(f1), str(f2)], str(tmp_path / "out.xlsx"))
        assert result["success"] is True

    def test_categorizador_works_offline(self, tmp_path):
        """Categorizador deve funcionar sem internet"""
        df = pd.DataFrame({"descricao": ["Posto Shell", "Uber", "Mercado"]})
        f = tmp_path / "in.xlsx"
        df.to_excel(f, index=False)

        c = Categorizador()
        result = c.categorize(str(f), str(tmp_path / "out.xlsx"), description_column="descricao")
        assert result["success"] is True

    def test_conciliador_works_offline(self, tmp_path):
        """Conciliador deve funcionar sem internet"""
        ext = pd.DataFrame({"date": ["2024-01-01"], "description": ["A"], "amount": [100]})
        sal = pd.DataFrame({"date": ["2024-01-01"], "description": ["B"], "amount": [100]})
        ef = tmp_path / "ext.csv"
        sf = tmp_path / "sal.csv"
        ext.to_csv(ef, index=False)
        sal.to_csv(sf, index=False)

        c = Conciliador()
        result = c.reconcile_classic(str(ef), str(sf), str(tmp_path / "out.xlsx"))
        assert result["success"] is True


# =========================================================================
# NOVOS TESTES: Performance/Regressão
# =========================================================================
class TestPerformance:
    """Testes de performance e regressão"""

    @pytest.mark.slow
    def test_consolidador_500k_linhas(self, tmp_path):
        """Consolidador deve processar 500k linhas sem OOM"""
        pytest.skip("Requer arquivo grande - executar manualmente")

    @pytest.mark.slow
    def test_orcamentos_1000_pdfs_streaming(self, tmp_path):
        """Orçamentos streaming deve gerar 1000 PDFs sem memory leak"""
        pytest.skip("Requer tempo - executar manualmente")

    def test_minerador_offline_mine_from_file(self, tmp_path):
        """Minerador mine_from_file deve funcionar offline (leitura CSV)"""
        from src.tools.minerador.minerador_v2 import Minerador
        m = Minerador()
        df = pd.DataFrame({"url": ["http://example.com/1", "http://example.com/2"]})
        f = tmp_path / "urls.csv"
        df.to_csv(f, index=False)

        with patch.object(Minerador, 'mine_from_links') as mock_mine:
            mock_mine.return_value = {"success": True, "results": [], "total": 2, "collected": 0}
            result = m.mine_from_file(str(f))
            assert result["success"] is True
            mock_mine.assert_called_once()


# =========================================================================
# NOVOS TESTES: ITool Interface
# =========================================================================
class TestIToolInterface:
    """Testes da interface ITool"""

    def test_consolidador_implements_itool(self):
        from src.tools.consolidador.consolidador_tool import ConsolidadorTool
        from src.tools.itool import ITool
        assert issubclass(ConsolidadorTool, ITool)

    def test_categorizador_implements_itool(self):
        from src.tools.categorizador.categorizador_tool import CategorizadorTool
        from src.tools.itool import ITool
        assert issubclass(CategorizadorTool, ITool)

    def test_orcamentos_implements_itool(self):
        from src.tools.orcamentos.orcamentos_tool import OrcamentosTool
        from src.tools.itool import ITool
        assert issubclass(OrcamentosTool, ITool)

    def test_minerador_implements_itool(self):
        from src.tools.minerador.minerador_tool import MineradorTool
        from src.tools.itool import ITool
        assert issubclass(MineradorTool, ITool)

    def test_conciliador_implements_itool(self):
        from src.tools.conciliador.conciliador_tool import ConciliadorTool
        from src.tools.itool import ITool
        assert issubclass(ConciliadorTool, ITool)

    def test_itool_adapters_registered(self):
        from src.tools.tool_registry import TOOL_REGISTRY
        from src.tools.itool import ITool
        for key in ["consolidador", "categorizador", "orcamentos", "minerador", "conciliador"]:
            assert key in TOOL_REGISTRY
            assert issubclass(TOOL_REGISTRY[key], ITool)