"""
Performance Monitor (APM) - Monitoramento de performance
Rastreia tempos de execução, chamadas lentas e métricas.
"""
import time
import threading
import logging
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps

log = logging.getLogger(__name__)


@dataclass
class Span:
    """Um span de performance (operação mediida)."""
    name: str
    start_time: float = 0
    end_time: float = 0
    duration_ms: float = 0
    status: str = "ok"
    metadata: Dict = field(default_factory=dict)

    @property
    def is_done(self) -> bool:
        return self.end_time > 0


@dataclass
class Metric:
    """Métrica acumulada."""
    name: str
    count: int = 0
    total_ms: float = 0
    min_ms: float = float("inf")
    max_ms: float = 0
    last_ms: float = 0

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.count if self.count > 0 else 0


class PerformanceMonitor:
    """Monitor de performance centralizado.

    Uso:
        apm = PerformanceMonitor.get_instance()

        # Manual
        span = apm.start("sync_upload")
        # ... operação ...
        apm.end(span)

        # Decorator
        @apm.track("supabase_query")
        def query_users():
            ...
    """

    _instance: Optional["PerformanceMonitor"] = None

    def __init__(self, slow_threshold_ms: float = 1000):
        self._slow_threshold_ms = slow_threshold_ms
        self._spans: List[Span] = []
        self._metrics: Dict[str, Metric] = {}
        self._active_spans: Dict[str, Span] = {}
        self._lock = threading.Lock()
        self._max_spans = 1000
        self._on_slow: Optional[Callable] = None

    @classmethod
    def get_instance(cls) -> "PerformanceMonitor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_slow_callback(self, callback: Callable):
        """Callback chamado quando operação lenta detectada."""
        self._on_slow = callback

    def start(self, name: str, metadata: Dict = None) -> Span:
        """Inicia um span de performance."""
        span = Span(
            name=name,
            start_time=time.monotonic(),
            metadata=metadata or {},
        )
        thread_id = threading.current_thread().ident
        key = f"{name}:{thread_id}"
        with self._lock:
            self._active_spans[key] = span
        return span

    def end(self, span: Span, status: str = "ok"):
        """Finaliza um span de performance."""
        span.end_time = time.monotonic()
        span.duration_ms = (span.end_time - span.start_time) * 1000
        span.status = status

        thread_id = threading.current_thread().ident
        key = f"{span.name}:{thread_id}"
        with self._lock:
            self._active_spans.pop(key, None)
            self._spans.append(span)

            # Manter apenas os últimos N spans
            if len(self._spans) > self._max_spans:
                self._spans = self._spans[-self._max_spans:]

            # Acumular métrica
            if span.name not in self._metrics:
                self._metrics[span.name] = Metric(name=span.name)
            m = self._metrics[span.name]
            m.count += 1
            m.total_ms += span.duration_ms
            m.min_ms = min(m.min_ms, span.duration_ms)
            m.max_ms = max(m.max_ms, span.duration_ms)
            m.last_ms = span.duration_ms

        # Log se lento
        if span.duration_ms > self._slow_threshold_ms:
            log.warning(
                "APM SLOW: %s took %.1fms (threshold: %.1fms)",
                span.name, span.duration_ms, self._slow_threshold_ms,
            )
            if self._on_slow:
                try:
                    self._on_slow(span)
                except Exception:
                    pass

        return span

    def track(self, name: str, metadata: Dict = None):
        """Decorator para rastrear performance de uma função.

        Uso:
            @apm.track("database_query")
            def query(sql):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                span = self.start(name, metadata)
                try:
                    result = func(*args, **kwargs)
                    self.end(span, "ok")
                    return result
                except Exception as e:
                    self.end(span, "error")
                    raise
            return wrapper
        return decorator

    def get_metrics(self) -> Dict[str, dict]:
        """Retorna todas as métricas acumuladas."""
        with self._lock:
            return {
                name: {
                    "count": m.count,
                    "avg_ms": round(m.avg_ms, 2),
                    "min_ms": round(m.min_ms, 2) if m.min_ms != float("inf") else 0,
                    "max_ms": round(m.max_ms, 2),
                    "last_ms": round(m.last_ms, 2),
                    "total_ms": round(m.total_ms, 2),
                }
                for name, m in self._metrics.items()
            }

    def get_slow_operations(self, limit: int = 10) -> List[dict]:
        """Retorna as operações mais lentas."""
        with self._lock:
            recent = [s for s in self._spans if s.is_done]
        recent.sort(key=lambda s: s.duration_ms, reverse=True)
        return [
            {
                "name": s.name,
                "duration_ms": round(s.duration_ms, 2),
                "status": s.status,
                "metadata": s.metadata,
            }
            for s in recent[:limit]
        ]

    def get_recent_spans(self, limit: int = 50) -> List[dict]:
        """Retorna spans recentes."""
        with self._lock:
            recent = list(self._spans[-limit:])
        return [
            {
                "name": s.name,
                "duration_ms": round(s.duration_ms, 2),
                "status": s.status,
                "start": s.start_time,
            }
            for s in recent if s.is_done
        ]

    def reset(self):
        """Reset todas as métricas."""
        with self._lock:
            self._spans.clear()
            self._metrics.clear()
            self._active_spans.clear()

    def get_summary(self) -> dict:
        """Retorna resumo geral de performance."""
        metrics = self.get_metrics()
        total_calls = sum(m["count"] for m in metrics.values())
        total_ms = sum(m["total_ms"] for m in metrics.values())
        slow_ops = self.get_slow_operations(5)

        return {
            "total_operations": total_calls,
            "total_time_ms": round(total_ms, 2),
            "avg_time_ms": round(total_ms / total_calls, 2) if total_calls > 0 else 0,
            "slow_operations": slow_ops,
            "metrics_count": len(metrics),
        }


# ── Context manager para uso fácil ──────────────────────────────────────────

class track_span:
    """Context manager para rastrear performance de um bloco.

    Uso:
        with track_span("my_operation"):
            do_work()
    """

    def __init__(self, name: str, metadata: Dict = None):
        self._name = name
        self._metadata = metadata
        self._span: Optional[Span] = None

    def __enter__(self):
        self._span = PerformanceMonitor.get_instance().start(self._name, self._metadata)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type else "ok"
        PerformanceMonitor.get_instance().end(self._span, status)
        return False
