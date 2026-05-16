import pytest
import pandas as pd
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.consolidador.consolidador import Consolidador
from src.tools.categorizador.categorizador import Categorizador
from src.tools.conciliador.conciliador import Conciliador


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

        from src.tools.consolidador.consolidador import Consolidador
        from src.tools.categorizador.categorizador import Categorizador

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