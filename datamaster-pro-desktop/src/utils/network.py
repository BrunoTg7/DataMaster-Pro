"""
Network utilities - Connection checker, retry, rate limiting
"""
import time
import logging
import threading
import requests
from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type

log = logging.getLogger(__name__)


def check_internet_connection(timeout: int = 3) -> bool:
    """Verifica se há conexão com a internet"""
    try:
        response = requests.get("https://httpbin.org/status/200", timeout=timeout)
        return response.status_code == 200
    except Exception:
        try:
            response = requests.get("https://google.com.br", timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """Decorator de retry com backoff exponencial.

    Uso:
        @retry(max_retries=3, exceptions=(ConnectionError, TimeoutError))
        def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    delay = min(base_delay * (2 ** attempt if exponential else 1), max_delay)
                    log.warning(
                        "Retry %d/%d for %s: %s (waiting %.1fs)",
                        attempt + 1, max_retries, func.__name__, e, delay,
                    )
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e)
                        except Exception:
                            pass
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


class RateLimiter:
    """Rate limiter baseado em token bucket thread-safe.

    Uso:
        limiter = RateLimiter(max_calls=10, period=60)
        limiter.wait()
        # ou
        with limiter:
            do_request()
    """

    def __init__(self, max_calls: int, period: float):
        self._max_calls = max_calls
        self._period = period
        self._tokens = max_calls
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        new_tokens = elapsed * (self._max_calls / self._period)
        self._tokens = min(self._max_calls, self._tokens + new_tokens)
        self._last_refill = now

    def wait(self) -> float:
        """Espera até que um token esteja disponível. Retorna o tempo esperado."""
        waited = 0.0
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return waited
                wait_time = (1 - self._tokens) * (self._period / self._max_calls)
            time.sleep(wait_time)
            waited += wait_time

    def __enter__(self):
        self.wait()
        return self

    def __exit__(self, *args):
        pass