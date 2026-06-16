"""
Tests for Circuit Breaker, Feature Flags, and Realtime Sync
"""
import pytest
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_import(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState
        assert CircuitBreaker is not None
        assert CircuitState is not None

    def test_initial_state_closed(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker("test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    def test_stays_closed_under_threshold(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker("test", failure_threshold=3)

        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerError
        cb = CircuitBreaker("test", failure_threshold=3)

        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

    def test_open_blocks_calls(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerError
        cb = CircuitBreaker("test", failure_threshold=2)

        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        with pytest.raises(CircuitBreakerError):
            cb.call(lambda: "should not run")

    def test_half_open_after_timeout(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)

        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)

        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        time.sleep(0.15)
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_success_resets_failure_count(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker("test", failure_threshold=3)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        cb.call(lambda: "ok")
        assert cb._failure_count == 0

    def test_reset(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker("test", failure_threshold=2)

        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_get_status(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker("test", failure_threshold=5, recovery_timeout=30)
        status = cb.get_status()
        assert status["name"] == "test"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["recovery_timeout"] == 30

    def test_get_circuit_breaker_singleton(self):
        from src.core.circuit_breaker import get_circuit_breaker
        cb1 = get_circuit_breaker("my_service")
        cb2 = get_circuit_breaker("my_service")
        assert cb1 is cb2

    def test_different_names_different_instances(self):
        from src.core.circuit_breaker import get_circuit_breaker
        cb1 = get_circuit_breaker("service_a")
        cb2 = get_circuit_breaker("service_b")
        assert cb1 is not cb2


class TestFeatureFlags:
    """Tests for FeatureFlagManager."""

    def test_import(self):
        from src.core.feature_flags import FeatureFlagManager, is_feature_enabled
        assert FeatureFlagManager is not None
        assert is_feature_enabled is not None

    def test_default_flag(self):
        from src.core.feature_flags import is_feature_enabled
        result = is_feature_enabled("dark_mode")
        assert result is True

    def test_unknown_flag_returns_false(self):
        from src.core.feature_flags import is_feature_enabled
        result = is_feature_enabled("nonexistent_flag_xyz")
        assert result is False

    def test_disabled_by_default(self):
        from src.core.feature_flags import is_feature_enabled
        result = is_feature_enabled("export_premium")
        assert result is False

    def test_override(self):
        from src.core.feature_flags import FeatureFlagManager
        mgr = FeatureFlagManager.get_instance()
        mgr.set_override("realtime_sync", False)
        assert mgr.is_enabled("realtime_sync") is False
        mgr.clear_override("realtime_sync")
        assert mgr.is_enabled("realtime_sync") is True

    def test_plan_restriction(self):
        from src.core.feature_flags import FeatureFlagManager
        mgr = FeatureFlagManager.get_instance()
        mgr.clear_override("export_premium")
        # export_premium requires "pro" plan and default is False
        # Gratis users are blocked by plan check
        assert mgr.is_enabled("export_premium", plan="gratis") is False
        # Pro users pass the plan check but default is False (no override)
        # Setting override to test plan gating works
        mgr.set_override("export_premium", True)
        assert mgr.is_enabled("export_premium", plan="pro") is True
        mgr.clear_override("export_premium")

    def test_rollout_percent(self):
        from src.core.feature_flags import FeatureFlagManager, KNOWN_FLAGS
        # browser_pool has 50% rollout
        flag = KNOWN_FLAGS["browser_pool"]
        assert flag.rollout_percent == 50

    def test_get_all_flags(self):
        from src.core.feature_flags import FeatureFlagManager
        mgr = FeatureFlagManager.get_instance()
        flags = mgr.get_all_flags()
        assert isinstance(flags, dict)
        assert len(flags) >= 7
        assert "realtime_sync" in flags
        assert "dark_mode" in flags

    def test_singleton(self):
        from src.core.feature_flags import FeatureFlagManager
        mgr1 = FeatureFlagManager.get_instance()
        mgr2 = FeatureFlagManager.get_instance()
        assert mgr1 is mgr2


class TestRealtimeSync:
    """Tests for RealtimeSync."""

    def test_import(self):
        from src.core.sync.realtime_sync import RealtimeSync, get_realtime_sync
        assert RealtimeSync is not None
        assert get_realtime_sync is not None

    def test_initial_state(self):
        from src.core.sync.realtime_sync import RealtimeSync
        mock_storage = MagicMock()
        sync = RealtimeSync(mock_storage)
        assert sync.is_running is False

    def test_set_on_change(self):
        from src.core.sync.realtime_sync import RealtimeSync
        mock_storage = MagicMock()
        sync = RealtimeSync(mock_storage)
        callback = MagicMock()
        sync.set_on_change(callback)
        assert sync._on_change is callback

    def test_singleton(self):
        from src.core.sync.realtime_sync import get_realtime_sync
        import src.core.sync.realtime_sync as mod
        # Reset singleton for test
        old = mod._instance
        mod._instance = None
        s1 = get_realtime_sync(MagicMock())
        s2 = get_realtime_sync()
        assert s1 is s2
        mod._instance = old
