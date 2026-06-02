"""
Tests for Memory Cache
"""
import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMemoryCache:
    """Tests for MemoryCache."""

    def test_import(self):
        from src.core.memory_cache import MemoryCache, get_cache
        assert MemoryCache is not None
        assert get_cache is not None

    def test_set_and_get(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"

    def test_ttl_expiry(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        cache.set("key1", "value1", ttl=0.1)
        assert cache.get("key1") == "value1"
        time.sleep(0.15)
        assert cache.get("key1") is None

    def test_delete(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_clear_all(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        cache.set("a:1", "v1")
        cache.set("b:2", "v2")
        cache.clear()
        assert cache.get("a:1") is None
        assert cache.get("b:2") is None

    def test_clear_by_prefix(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        cache.set("stats:user1", "data1")
        cache.set("stats:user2", "data2")
        cache.set("other:key", "data3")
        cache.clear(prefix="stats:")
        assert cache.get("stats:user1") is None
        assert cache.get("stats:user2") is None
        assert cache.get("other:key") == "data3"

    def test_get_or_set(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        call_count = [0]

        def factory():
            call_count[0] += 1
            return "computed"

        result = cache.get_or_set("key", factory)
        assert result == "computed"
        assert call_count[0] == 1

        # Second call uses cache
        result = cache.get_or_set("key", factory)
        assert result == "computed"
        assert call_count[0] == 1

    def test_decorator(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        call_count = [0]

        @cache.cached(ttl=60, key_prefix="test")
        def expensive_func(x):
            call_count[0] += x
            return x * 2

        result = expensive_func(5)
        assert result == 10
        assert call_count[0] == 5

        # Second call uses cache
        result = expensive_func(5)
        assert result == 10
        assert call_count[0] == 5  # Not called again

        # Different arg creates new cache entry
        result = expensive_func(3)
        assert result == 6
        assert call_count[0] == 8  # 5 + 3

    def test_max_size_eviction(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict oldest
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_stats(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        cache.set("key", "value")
        cache.get("key")  # hit
        cache.get("missing")  # miss
        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1

    def test_singleton(self):
        from src.core.memory_cache import get_cache
        c1 = get_cache()
        c2 = get_cache()
        assert c1 is c2

    def test_complex_values(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"key": "value", "nested": {"a": 1}})
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict")["nested"]["a"] == 1

    def test_overwrite(self):
        from src.core.memory_cache import MemoryCache
        cache = MemoryCache()
        cache.set("key", "old")
        cache.set("key", "new")
        assert cache.get("key") == "new"
