import pytest
import pandas as pd
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.consolidador.consolidador_v2 import Consolidador
from src.tools.categorizador.categorizador_v2 import Categorizador
from src.tools.conciliador.conciliador_v2 import Conciliador


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