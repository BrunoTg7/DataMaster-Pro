"""
Memory Cache - Cache em memória com TTL para stats e dados
Substitui Redis para uso em desktop. Zero dependências externas.
"""
import time
import threading
import logging
from typing import Optional, Any, Dict
from functools import wraps

log = logging.getLogger(__name__)


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.monotonic() + ttl

    @property
    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class MemoryCache:
    """Cache em memória com TTL e limpeza automática.

    Uso:
        cache = MemoryCache(default_ttl=300)

        # Definir
        cache.set("user_stats:user123", {"rows": 100, "execs": 5})

        # Obter
        stats = cache.get("user_stats:user123")

        # Decorator
        @cache.cached(ttl=60)
        def get_heavy_data():
            ...
    """

    _instance: Optional["MemoryCache"] = None

    def __init__(self, default_ttl: float = 300, max_size: int = 1000):
        self._store: Dict[str, _CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

        # Limpeza periódica a cada 60s
        self._cleanup_interval = 60
        self._start_cleanup_thread()

    @classmethod
    def get_instance(cls) -> "MemoryCache":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor do cache. Retorna default se ausente ou expirado."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return default
            if entry.is_expired:
                del self._store[key]
                self._misses += 1
                return default
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Define valor no cache com TTL opcional."""
        ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            # Evict se atingiu limite
            if len(self._store) >= self._max_size and key not in self._store:
                self._evict_expired()
                if len(self._store) >= self._max_size:
                    self._evict_oldest()
            self._store[key] = _CacheEntry(value, ttl)

    def delete(self, key: str):
        """Remove valor do cache."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self, prefix: str = ""):
        """Limpa cache. Se prefix fornecido, limpa só chaves com esse prefixo."""
        with self._lock:
            if prefix:
                keys = [k for k in self._store if k.startswith(prefix)]
                for k in keys:
                    del self._store[k]
                log.debug("Cache limpo: %d chaves com prefixo '%s'", len(keys), prefix)
            else:
                count = len(self._store)
                self._store.clear()
                log.debug("Cache limpo: %d chaves", count)

    def get_or_set(self, key: str, factory, ttl: Optional[float] = None) -> Any:
        """Obtém do cache ou executa factory e armazena o resultado."""
        value = self.get(key)
        if value is not None:
            return value
        value = factory()
        self.set(key, value, ttl)
        return value

    def cached(self, ttl: Optional[float] = None, key_prefix: str = ""):
        """Decorator que cacheia resultado de função.

        Uso:
            @cache.cached(ttl=60, key_prefix="stats")
            def get_stats(user_id):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Gerar chave baseada em args
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

                result = self.get(cache_key)
                if result is not None:
                    return result

                result = func(*args, **kwargs)
                if result is not None:
                    self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache."""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._store),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{self._hits / total * 100:.1f}%" if total > 0 else "N/A",
            }

    def _evict_expired(self):
        """Remove entradas expiradas."""
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if v.expires_at < now]
        for k in expired:
            del self._store[k]
        if expired:
            log.debug("Cache: evicted %d expired entries", len(expired))

    def _evict_oldest(self):
        """Remove a entrada mais antiga."""
        if not self._store:
            return
        oldest_key = min(self._store, key=lambda k: self._store[k].expires_at)
        del self._store[oldest_key]

    def _start_cleanup_thread(self):
        """Inicia thread de limpeza periódica."""
        def cleanup_loop():
            while True:
                time.sleep(self._cleanup_interval)
                try:
                    with self._lock:
                        before = len(self._store)
                        self._evict_expired()
                        after = len(self._store)
                        if before != after:
                            log.debug(
                                "Cache cleanup: %d → %d entries",
                                before, after,
                            )
                except Exception as e:
                    log.error("Cache cleanup error: %s", e)

        t = threading.Thread(target=cleanup_loop, daemon=True, name="cache-cleanup")
        t.start()


# ── Accessor global ──────────────────────────────────────────────────────────

def get_cache() -> MemoryCache:
    """Retorna instância singleton do cache."""
    return MemoryCache.get_instance()
