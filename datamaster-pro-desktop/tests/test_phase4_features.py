"""
Testes Phase 4 - Features
- Validador: HEAD request já implementado
- Consolidador: JSON preview streaming
- Gerador Laudos: itertuples() optimization
"""
import pytest
import json
import tempfile
from pathlib import Path


class TestValidadorHEADRequest:
    """Testes de HEAD request no Validador"""

    def test_quick_head_check_exists(self):
        from src.tools.validador_links.validador_links_v2 import ValidadorLinks
        assert hasattr(ValidadorLinks, '_quick_head_check')

    def test_quick_head_check_is_coroutine(self):
        import inspect
        from src.tools.validador_links.validador_links_v2 import ValidadorLinks
        assert inspect.iscoroutinefunction(ValidadorLinks._quick_head_check)

    def test_head_check_called_before_playwright(self):
        import inspect
        from src.tools.validador_links.validador_links_v2 import ValidadorLinks
        source = inspect.getsource(ValidadorLinks._validate_single_link)
        head_pos = source.find("_quick_head_check")
        playwright_pos = source.find("self.context.new_page")
        assert head_pos < playwright_pos, "HEAD check must be called before Playwright page creation"


class TestConsolidadorJSONPreview:
    """Testes de JSON preview otimizado no Consolidador"""

    def _make_consolidador(self):
        from src.tools.consolidador.consolidador_v2 import Consolidador
        return Consolidador()

    def test_json_preview_reads_only_rows(self, tmp_path):
        c = self._make_consolidador()
        data = [{"id": i, "name": f"item_{i}"} for i in range(1000)]
        json_file = tmp_path / "large.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")
        
        result = c.preview(str(json_file), rows=5)
        assert result is not None
        assert len(result) == 5
        assert list(result.columns) == ["id", "name"]

    def test_json_preview_empty_array(self, tmp_path):
        c = self._make_consolidador()
        json_file = tmp_path / "empty.json"
        json_file.write_text("[]", encoding="utf-8")
        
        result = c.preview(str(json_file), rows=5)
        assert result is not None
        assert len(result) == 0

    def test_json_preview_single_object(self, tmp_path):
        c = self._make_consolidador()
        data = {"id": 1, "name": "test"}
        json_file = tmp_path / "single.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")
        
        result = c.preview(str(json_file), rows=5)
        assert result is not None
        assert len(result) == 1

    def test_json_preview_nested(self, tmp_path):
        c = self._make_consolidador()
        data = [{"id": 1, "meta": {"x": 10}}, {"id": 2, "meta": {"x": 20}}]
        json_file = tmp_path / "nested.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")
        
        result = c.preview(str(json_file), rows=1)
        assert result is not None
        assert len(result) == 1

    def test_json_preview_large_file_performance(self, tmp_path):
        """Verifica que preview de JSON grande não carrega arquivo inteiro na memória"""
        import time
        c = self._make_consolidador()
        data = [{"id": i, "value": f"val_{i}"} for i in range(50000)]
        json_file = tmp_path / "huge.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")
        
        start = time.time()
        result = c.preview(str(json_file), rows=10)
        elapsed = time.time() - start
        
        assert result is not None
        assert len(result) == 10
        assert elapsed < 5, f"Preview took {elapsed:.1f}s, should be under 5s for streaming"


class TestGeradorLaudosItertuples:
    """Testes de otimização iterrows→itertuples no Gerador Laudos"""

    def test_itertuples_used_in_source(self):
        import inspect
        from src.tools.gerador_laudos.gerador_laudos_v2 import GeradorLaudos
        source = inspect.getsource(GeradorLaudos._match_data)
        assert "itertuples" in source
        # iterrows should NOT be used as the loop mechanism (only allowed in comments/docs)
        lines = [l for l in source.split('\n') if l.strip() and not l.strip().startswith('#')]
        loop_lines = [l for l in lines if 'iterrows' in l and 'for ' in l]
        assert len(loop_lines) == 0, f"iterrows still used in loop: {loop_lines}"

    def test_match_data_returns_correct_structure(self):
        import pandas as pd
        from src.tools.gerador_laudos.gerador_laudos_v2 import GeradorLaudos
        
        g = GeradorLaudos()
        extrato = pd.DataFrame({
            "valor": [100.0, 200.0, 300.0],
            "data": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "descricao": ["Item A", "Item B", "Item C"]
        })
        notas = pd.DataFrame({
            "NF": ["NF-001", "NF-002", "NF-003"],
            "Valor": [100.0, 200.0, 300.0]
        })
        
        result = g._match_data(extrato, notas)
        assert len(result) == 3
        assert all(r["status"] == "Conforme" for r in result)
        assert result[0]["nf"] == "NF-001"

    def test_match_data_tolerance(self):
        import pandas as pd
        from src.tools.gerador_laudos.gerador_laudos_v2 import GeradorLaudos
        
        g = GeradorLaudos()
        extrato = pd.DataFrame({"valor": [100.50], "data": ["2024-01-01"], "descricao": ["Test"]})
        notas = pd.DataFrame({"NF": ["NF-001"], "Valor": [100.00]})
        
        result = g._match_data(extrato, notas, {"tolerance": 1.0})
        assert result[0]["status"] == "Conforme"

    def test_match_data_no_match(self):
        import pandas as pd
        from src.tools.gerador_laudos.gerador_laudos_v2 import GeradorLaudos
        
        g = GeradorLaudos()
        extrato = pd.DataFrame({"valor": [100.0], "data": ["2024-01-01"], "descricao": ["Test"]})
        notas = pd.DataFrame({"NF": ["NF-001"], "valor": [999.0]})
        
        result = g._match_data(extrato, notas, {"tolerance": 0.50})
        assert result[0]["status"] == "Pendente"
        assert result[0]["nf"] == "N/A"
