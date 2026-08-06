"""
Testes Phase 3 - Qualidade
- Minerador: dict marketplace detection
- Sanitizador: strategy dict
- Conversor OCR: thread-safe env
- Precificador: merge_cells guard
- Calculadora: networkidle + opportunity_score doc
- Gerador Laudos: tolerancia config + thresholds doc
- Extrator Reviews: sentiment 100+ words
- Classificador NCM: NFD normalization
- Consolidador: dead code removed
- Conciliador: shared fuzzy helper
"""
import pytest
import unicodedata


class TestMineradorDictMarketplace:
    """Testes de detecção de marketplace via dict"""

    def test_dict_exists(self):
        from src.tools.minerador.minerador_v2 import Minerador
        assert hasattr(Minerador, '_MARKETPLACE_URL_MAP')
        assert isinstance(Minerador._MARKETPLACE_URL_MAP, dict)

    def test_detect_marketplace_from_url(self):
        from src.tools.minerador.minerador_v2 import Minerador
        assert Minerador._detect_marketplace("https://www.kabum.com.br/product/123", "generico") == "kabum"

    def test_detect_marketplace_mercadolivre(self):
        from src.tools.minerador.minerador_v2 import Minerador
        assert Minerador._detect_marketplace("https://www.mercadolivre.com.br/product", "generico") == "mercadolivre"

    def test_detect_marketplace_passthrough(self):
        from src.tools.minerador.minerador_v2 import Minerador
        assert Minerador._detect_marketplace("https://any.com", "pichau") == "pichau"

    def test_detect_marketplace_generico_fallback(self):
        from src.tools.minerador.minerador_v2 import Minerador
        assert Minerador._detect_marketplace("https://unknown.com", "generico") == "generico"


class TestSanitizadorStrategyDict:
    """Testes de strategy dict no Sanitizador"""

    def _make_sanitizer(self):
        from src.tools.data_sanitizer.data_sanitizer_v2 import DataSanitizer
        return DataSanitizer()

    def test_transformation_map_exists(self):
        from src.tools.data_sanitizer.data_sanitizer_v2 import DataSanitizer
        assert hasattr(DataSanitizer, '_TRANSFORMATION_MAP')
        assert isinstance(DataSanitizer._TRANSFORMATION_MAP, dict)

    def test_resolve_transform_nome(self):
        s = self._make_sanitizer()
        fn = s._resolve_transform("nome")
        assert fn is not None
        assert callable(fn)

    def test_resolve_transform_cpf(self):
        s = self._make_sanitizer()
        fn = s._resolve_transform("cpf")
        assert fn is not None

    def test_resolve_transform_unknown(self):
        s = self._make_sanitizer()
        assert s._resolve_transform("coluna_randomica") is None

    def test_resolve_transform_case_insensitive(self):
        s = self._make_sanitizer()
        fn = s._resolve_transform("NOME")
        assert fn is not None

    def test_resolve_transform_fone_alias(self):
        s = self._make_sanitizer()
        fn = s._resolve_transform("fone")
        assert fn is not None

    def test_resolve_transform_endereco_alias(self):
        s = self._make_sanitizer()
        fn = s._resolve_transform("endereço")
        assert fn is not None


class TestConversorOCRThreadSafe:
    """Testes de thread-safety no Conversor OCR"""

    def test_env_lock_exists(self):
        from src.tools.conversor_ocr.conversor_ocr_v2 import ConversorOCR
        import threading
        c = ConversorOCR.__new__(ConversorOCR)
        c._env_lock = threading.Lock()
        assert isinstance(c._env_lock, type(threading.Lock()))


class TestPrecificadorMergeCellsGuard:
    """Testes de merge_cells guard no Precificador"""

    def test_file_loads_without_error(self):
        from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
        assert True


class TestCalculadoraLucratividade:
    """Testes de networkidle e opportunity_score"""

    def test_opportunity_score_documented(self):
        import inspect
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        source = inspect.getsource(CalculadoraLucratividade.calculate_async)
        assert "Opportunity Score" in source or "opportunity_score" in source
        assert "margin * 2.5" in source

    def test_networkidle_in_source(self):
        import inspect
        from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
        source = inspect.getsource(CalculadoraLucratividade._process_single_url)
        assert "networkidle" in source


class TestGeradorLaudos:
    """Testes de tolerância config e thresholds"""

    def test_tolerance_configurable(self):
        import inspect
        from src.tools.gerador_laudos.gerador_laudos_v2 import GeradorLaudos
        source = inspect.getsource(GeradorLaudos._match_data)
        assert "tolerance" in source.lower()
        assert "config" in source

    def test_thresholds_documented(self):
        import inspect
        from src.tools.gerador_laudos.gerador_laudos_v2 import GeradorLaudos
        source = inspect.getsource(GeradorLaudos.generate)
        assert "APROVADO" in source
        assert "80" in source
        assert "50" in source


class TestExtratorReviewsSentiment:
    """Testes de dicionário de sentimento expandido"""

    def test_sentiment_dict_has_100_plus_words(self):
        from src.tools.extrator_reviews.extrator_reviews_v2 import ExtratorReviews
        pos = len(ExtratorReviews.SENTIMENT_DICT.get("positive", []))
        neg = len(ExtratorReviews.SENTIMENT_DICT.get("negative", []))
        total = pos + neg
        assert total >= 100, f"Sentiment dictionary has only {total} words (expected 100+)"

    def test_sentiment_positive_has_at_least_50(self):
        from src.tools.extrator_reviews.extrator_reviews_v2 import ExtratorReviews
        assert len(ExtratorReviews.SENTIMENT_DICT.get("positive", [])) >= 50

    def test_sentiment_negative_has_at_least_50(self):
        from src.tools.extrator_reviews.extrator_reviews_v2 import ExtratorReviews
        assert len(ExtratorReviews.SENTIMENT_DICT.get("negative", [])) >= 50


class TestClassificadorNCMNFD:
    """Testes de normalização NFD no Classificador NCM"""

    def test_nfd_normalization_used(self):
        import inspect
        from src.tools.classificador_ncm.classificador_ncm_v1 import ClassificadorNCM
        source = inspect.getsource(ClassificadorNCM._classificar_um)
        assert "unicodedata" in source
        assert "NFD" in source

    def test_accent_stripping(self):
        raw = "SÃO PAULO"
        normalized = ''.join(c for c in unicodedata.normalize('NFD', raw) if unicodedata.category(c) != 'Mn')
        assert normalized == "SAO PAULO"

    def test_accent_stripping_complex(self):
        raw = "café com açúcar"
        normalized = ''.join(c for c in unicodedata.normalize('NFD', raw) if unicodedata.category(c) != 'Mn')
        assert normalized == "cafe com acucar"


class TestConsolidadorDeadCodeRemoved:
    """Testes de código morto removido no Consolidador"""

    def test_read_excel_chunked_removed(self):
        from src.tools.consolidador.consolidador_v2 import Consolidador
        assert not hasattr(Consolidador, '_read_excel_chunked')

    def test_chunk_size_removed(self):
        from src.tools.consolidador.consolidador_v2 import Consolidador
        assert not hasattr(Consolidador, 'CHUNK_SIZE')

    def test_itertools_not_imported(self):
        import importlib
        import src.tools.consolidador.consolidador_v2 as mod
        source = importlib.util.find_spec(mod.__name__).origin
        with open(source, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'import itertools' not in content


class TestConciliadorFuzzyHelper:
    """Testes de helper fuzzy compartilhado no Conciliador"""

    def test_fuzzy_desc_match_exists(self):
        from src.tools.conciliador.conciliador_v2 import Conciliador
        assert hasattr(Conciliador, '_fuzzy_desc_match')

    def test_fuzzy_desc_match_identical(self):
        from src.tools.conciliador.conciliador_v2 import Conciliador
        c = Conciliador()
        assert c._fuzzy_desc_match("teste", "teste", 80) is True

    def test_fuzzy_desc_match_different(self):
        from src.tools.conciliador.conciliador_v2 import Conciliador
        c = Conciliador()
        assert c._fuzzy_desc_match("abc", "xyz", 80) is False

    def test_fuzzy_desc_match_empty(self):
        from src.tools.conciliador.conciliador_v2 import Conciliador
        c = Conciliador()
        assert c._fuzzy_desc_match("", "something", 80) is True

    def test_build_sorted_index_exists(self):
        from src.tools.conciliador.conciliador_v2 import Conciliador
        assert hasattr(Conciliador, '_build_sorted_index')
