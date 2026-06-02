"""
Circuit Breaker - Padrão para prevenir falhas em cascata
Quando um serviço externo falha muitas vezes, o circuit breaker "abre"
e bloqueia chamadas temporariamente, evitando sobrecarregar o serviço.

Estados:
  CLOSED   → Normal, chamadas passam
  OPEN     → Serviço com falha, chamadas bloqueadas
  HALF_OPEN → Testando se o serviço voltou

Inclui retry automático com backoff exponencial dentro do circuit breaker.
"""
import time
import threading
import logging
from enum import Enum
from typing import Callable, Optional, Any

log = logging.getLogger(__name__)

# Configuração de retry
RETRY_MAX = 2
RETRY_BASE_DELAY = 0.5
RETRY_MAX_DELAY = 5.0


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Exceção lançada quando o circuit breaker está aberto."""
    pass


class CircuitBreaker:
    """Implementa o padrão Circuit Breaker para proteger chamadas externas.

    Uso:
        cb = CircuitBreaker("supabase", failure_threshold=5, recovery_timeout=60)

        try:
            result = cb.call(supabase.table("users").execute)
        except CircuitBreakerError:
            # Serviço indisponível, usar fallback
            ...
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self.recovery_timeout:
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        log.info(
                            "[%s] Circuit breaker: OPEN → HALF_OPEN (after %.1fs)",
                            self.name, elapsed,
                        )
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executa uma função protegida pelo circuit breaker com retry.

        Raises:
            CircuitBreakerError: Se o circuit breaker estiver aberto.
        """
        # Verificação inicial do circuit breaker
        current_state = self.state
        if current_state == CircuitState.OPEN:
            log.warning("[%s] Circuit breaker OPEN — chamada bloqueada", self.name)
            raise CircuitBreakerError(
                f"Service '{self.name}' is unavailable (circuit breaker OPEN). "
                f"Retry in {self.recovery_timeout}s."
            )
        if current_state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerError(f"Service '{self.name}' testing recovery.")
                self._half_open_calls += 1

        # Retry loop — contagem de falhas do circuit breaker é separada
        last_exception = None
        for attempt in range(RETRY_MAX + 1):
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except CircuitBreakerError:
                raise
            except Exception as e:
                last_exception = e
                if attempt < RETRY_MAX:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                    log.warning(
                        "[%s] Retry %d/%d after %.1fs: %s",
                        self.name, attempt + 1, RETRY_MAX, delay, e,
                    )
                    time.sleep(delay)
                else:
                    # Último attempt — registra falha no circuit breaker
                    self._on_failure()
                    raise

        raise last_exception

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    log.info("[%s] Circuit breaker: HALF_OPEN → CLOSED", self.name)
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                log.warning(
                    "[%s] Circuit breaker: HALF_OPEN → OPEN (test failed)",
                    self.name,
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                log.warning(
                    "[%s] Circuit breaker: CLOSED → OPEN (%d failures)",
                    self.name, self._failure_count,
                )

    def reset(self):
        """Força reset do circuit breaker para CLOSED."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            log.info("[%s] Circuit breaker reset to CLOSED", self.name)

    def get_status(self) -> dict:
        """Retorna status atual do circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "last_failure": self._last_failure_time,
            "recovery_timeout": self.recovery_timeout,
        }


# ── Registry global de circuit breakers ──────────────────────────────────────

_breakers: dict[str, CircuitBreaker] = {}
_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> CircuitBreaker:
    """Obtém ou cria um circuit breaker pelo nome."""
    with _lock:
        if name not in _breakers:
            _breakers[name] = CircuitBreaker(
                name, failure_threshold, recovery_timeout
            )
        return _breakers[name]


def get_all_breakers() -> dict[str, CircuitBreaker]:
    """Retorna todos os circuit breakers registrados."""
    return dict(_breakers)
