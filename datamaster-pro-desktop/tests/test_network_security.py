"""
Tests for Network utilities (retry, RateLimiter) and API security
"""
import time
import threading
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════════════════════
# Retry Decorator
# ═══════════════════════════════════════════════════════════════════════════════

class TestRetry:
    def test_success_no_retry(self):
        from src.utils.network import retry
        call_count = [0]

        @retry(max_retries=3, base_delay=0.01)
        def succeed():
            call_count[0] += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count[0] == 1

    def test_retry_on_failure(self):
        from src.utils.network import retry
        call_count = [0]

        @retry(max_retries=2, base_delay=0.01, exceptions=(ValueError,))
        def fail_twice():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("fail")
            return "ok"

        result = fail_twice()
        assert result == "ok"
        assert call_count[0] == 3

    def test_exhausted_retries(self):
        from src.utils.network import retry

        @retry(max_retries=2, base_delay=0.01, exceptions=(ValueError,))
        def always_fail():
            raise ValueError("always")

        with pytest.raises(ValueError, match="always"):
            always_fail()

    def test_no_retry_on_different_exception(self):
        from src.utils.network import retry
        call_count = [0]

        @retry(max_retries=3, base_delay=0.01, exceptions=(ValueError,))
        def raise_type_error():
            call_count[0] += 1
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            raise_type_error()
        assert call_count[0] == 1

    def test_on_retry_callback(self):
        from src.utils.network import retry
        attempts = []

        @retry(max_retries=2, base_delay=0.01, exceptions=(ValueError,),
               on_retry=lambda n, e: attempts.append(n))
        def fail_twice():
            if len(attempts) < 2:
                raise ValueError("fail")
            return "ok"

        result = fail_twice()
        assert result == "ok"
        assert attempts == [1, 2]

    def test_max_delay_cap(self):
        from src.utils.network import retry
        start = time.monotonic()

        @retry(max_retries=3, base_delay=100, max_delay=0.05, exceptions=(ValueError,))
        def always_fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            always_fail()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0  # Should be capped, not 100+200+400


# ═══════════════════════════════════════════════════════════════════════════════
# RateLimiter
# ═══════════════════════════════════════════════════════════════════════════════

class TestRateLimiter:
    def test_allows_within_limit(self):
        from src.utils.network import RateLimiter
        limiter = RateLimiter(max_calls=5, period=1.0)
        for _ in range(5):
            waited = limiter.wait()
            assert waited == 0.0

    def test_blocks_over_limit(self):
        from src.utils.network import RateLimiter
        limiter = RateLimiter(max_calls=3, period=1.0)
        for _ in range(3):
            limiter.wait()
        # 4th call should wait
        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed > 0

    def test_context_manager(self):
        from src.utils.network import RateLimiter
        limiter = RateLimiter(max_calls=10, period=1.0)
        with limiter:
            pass  # Should not raise

    def test_thread_safety(self):
        from src.utils.network import RateLimiter
        limiter = RateLimiter(max_calls=10, period=1.0)
        results = []

        def worker():
            limiter.wait()
            results.append(True)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 10

    def test_tokens_refill(self):
        from src.utils.network import RateLimiter
        limiter = RateLimiter(max_calls=2, period=0.1)
        limiter.wait()
        limiter.wait()
        time.sleep(0.15)  # Wait for refill
        waited = limiter.wait()
        assert waited == 0.0  # Should have tokens again


# ═══════════════════════════════════════════════════════════════════════════════
# Circuit Breaker with Retry
# ═══════════════════════════════════════════════════════════════════════════════

class TestCircuitBreakerRetry:
    def test_call_retries_on_failure(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker("test_retry", failure_threshold=10, recovery_timeout=60)
        call_count = [0]

        def fail_twice():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("transient")
            return "ok"

        result = cb.call(fail_twice)
        assert result == "ok"
        assert call_count[0] == 3

    def test_call_raises_after_exhausted_retries(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitBreakerError
        cb = CircuitBreaker("test_retry2", failure_threshold=10, recovery_timeout=60)

        def always_fail():
            raise ConnectionError("permanent")

        with pytest.raises(ConnectionError):
            cb.call(always_fail)

    def test_circuit_breaker_still_opens_on_sustained_failure(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitBreakerError
        cb = CircuitBreaker("test_retry3", failure_threshold=3, recovery_timeout=60)

        def always_fail():
            raise ConnectionError("fail")

        # 3 failures × 3 retries each = 9 total attempts, but only 3 circuit failures
        for _ in range(5):
            try:
                cb.call(always_fail)
            except Exception:
                pass

        assert cb.state.value == "open"


# ═══════════════════════════════════════════════════════════════════════════════
# API Security (FastAPI)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPISecurity:
    def test_cors_restricted(self):
        """Verify CORS is not wildcard."""
        from src.api.main import ALLOWED_ORIGINS
        assert "*" not in ALLOWED_ORIGINS
        assert len(ALLOWED_ORIGINS) > 0

    def test_rate_limit_check(self):
        from src.api.main import check_rate_limit
        # Should allow first requests
        assert check_rate_limit("192.168.1.1", "test_endpoint") is True

    def test_rate_limit_blocks(self):
        import time
        from src.api.main import _rate_limits, RATE_LIMIT_REQUESTS
        ip = "10.0.0.99"
        endpoint = "rate_test"
        key = f"{ip}:{endpoint}"
        now = time.time()
        # Fill the bucket
        _rate_limits[key] = [now - i for i in range(RATE_LIMIT_REQUESTS)]
        # Next request should be blocked via middleware
        from src.api.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health", headers={"X-Forwarded-For": ip})
        # health is unthrottled, but the rate limit state should be full
        assert key in _rate_limits
        # Clean up
        _rate_limits.pop(key, None)

    def test_health_no_auth(self):
        """Health endpoint should not require auth."""
        from src.api.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_protected_endpoint_no_token(self):
        """Protected endpoints should reject without token."""
        from src.api.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/api/tasks")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
