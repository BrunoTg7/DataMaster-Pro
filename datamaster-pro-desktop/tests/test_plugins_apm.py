"""
Tests for PluginRegistry, PerformanceMonitor (APM), Container, and Domain Entities
"""
import time
import threading
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════════════════════
# PluginRegistry
# ═══════════════════════════════════════════════════════════════════════════════

class MockTool:
    TOOL_KEY = "mock_tool"

class MockTool2:
    pass


class TestPluginRegistryBasic:
    def setup_method(self):
        from src.domain.plugin_registry import PluginRegistry
        PluginRegistry._instance = None
        self.reg = PluginRegistry.get_instance()

    def test_singleton(self):
        from src.domain.plugin_registry import PluginRegistry
        r1 = PluginRegistry.get_instance()
        r2 = PluginRegistry.get_instance()
        assert r1 is r2

    def test_register_tool(self):
        from src.domain.entities import ToolMetadata
        meta = ToolMetadata(key="test_tool", name="Test Tool")
        self.reg.register("test_tool", MockTool, meta, "test_module")
        assert self.reg.is_registered("test_tool")
        assert self.reg.get_tool_class("test_tool") is MockTool
        assert self.reg.get_metadata("test_tool").name == "Test Tool"
        assert self.reg.get_page_module("test_tool") == "test_module"

    def test_unregister(self):
        self.reg.register("to_remove", MockTool)
        assert self.reg.is_registered("to_remove")
        self.reg.unregister("to_remove")
        assert not self.reg.is_registered("to_remove")

    def test_get_all_keys(self):
        self.reg.register("key_a", MockTool)
        self.reg.register("key_b", MockTool2)
        keys = self.reg.get_all_keys()
        assert "key_a" in keys
        assert "key_b" in keys

    def test_get_all_page_modules(self):
        self.reg.register("tool_x", MockTool, page_module="mod_x")
        pages = self.reg.get_all_page_modules()
        assert pages.get("tool_x") == "mod_x"

    def test_register_page_module(self):
        self.reg.register("tool_y", MockTool)
        self.reg.register_page_module("tool_y", "mod_y")
        assert self.reg.get_page_module("tool_y") == "mod_y"

    def test_discover_runs_without_error(self):
        self.reg.discover(tools_dir="/nonexistent/path")


# ═══════════════════════════════════════════════════════════════════════════════
# PerformanceMonitor (APM)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerformanceMonitor:
    def setup_method(self):
        from src.core.apm import PerformanceMonitor
        PerformanceMonitor._instance = None
        self.apm = PerformanceMonitor.get_instance()

    def test_singleton(self):
        from src.core.apm import PerformanceMonitor
        a1 = PerformanceMonitor.get_instance()
        a2 = PerformanceMonitor.get_instance()
        assert a1 is a2

    def test_start_end(self):
        span = self.apm.start("test_op")
        assert span.name == "test_op"
        assert span.start_time > 0
        time.sleep(0.02)
        self.apm.end(span, "ok")
        assert span.is_done
        assert span.duration_ms > 0
        assert span.status == "ok"

    def test_metric_accumulation(self):
        s1 = self.apm.start("op_a")
        time.sleep(0.01)
        self.apm.end(s1)

        s2 = self.apm.start("op_a")
        time.sleep(0.01)
        self.apm.end(s2)

        metrics = self.apm.get_metrics()
        assert "op_a" in metrics
        assert metrics["op_a"]["count"] == 2
        assert metrics["op_a"]["avg_ms"] > 0

    def test_slow_threshold_callback(self):
        slow_calls = []
        # Create fresh instance with threshold=0 so any duration triggers
        from src.core.apm import PerformanceMonitor
        apm = PerformanceMonitor(slow_threshold_ms=0)
        apm.set_slow_callback(lambda span: slow_calls.append(span.name))

        span = apm.start("slow_op")
        time.sleep(0.05)
        apm.end(span)
        assert span.duration_ms > 0, f"duration was {span.duration_ms}"
        assert len(slow_calls) == 1, f"expected 1 slow call, got {len(slow_calls)}: {slow_calls}"

    def test_context_manager(self):
        from src.core.apm import track_span
        with track_span("ctx_test"):
            time.sleep(0.01)
        metrics = self.apm.get_metrics()
        assert "ctx_test" in metrics
        assert metrics["ctx_test"]["count"] == 1

    def test_decorator(self):
        @self.apm.track("decorated_op")
        def my_func():
            time.sleep(0.01)
            return 42

        result = my_func()
        assert result == 42
        metrics = self.apm.get_metrics()
        assert "decorated_op" in metrics

    def test_decorator_on_exception(self):
        @self.apm.track("failing_op")
        def bad_func():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            bad_func()

        metrics = self.apm.get_metrics()
        assert "failing_op" in metrics

    def test_get_slow_operations(self):
        span = self.apm.start("slow_1")
        span.duration_ms = 500
        span.end_time = span.start_time + 0.5
        self.apm._spans.append(span)

        slow = self.apm.get_slow_operations(5)
        assert len(slow) >= 1
        assert slow[0]["name"] == "slow_1"

    def test_get_summary(self):
        span = self.apm.start("summary_op")
        self.apm.end(span)
        summary = self.apm.get_summary()
        assert "total_operations" in summary
        assert "total_time_ms" in summary
        assert summary["total_operations"] >= 1

    def test_reset(self):
        span = self.apm.start("to_reset")
        self.apm.end(span)
        self.apm.reset()
        assert self.apm.get_metrics() == {}

    def test_max_spans_limit(self):
        apm2 = type(self.apm)(slow_threshold_ms=999999)
        apm2._max_spans = 5
        for i in range(10):
            s = apm2.start(f"span_{i}")
            apm2.end(s)
        assert len(apm2._spans) == 5

    def test_thread_safety(self):
        errors = []

        def worker(idx):
            try:
                for _ in range(50):
                    s = self.apm.start(f"thread_{idx}")
                    time.sleep(0.001)
                    self.apm.end(s)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        metrics = self.apm.get_metrics()
        assert sum(m["count"] for m in metrics.values()) == 200


# ═══════════════════════════════════════════════════════════════════════════════
# Container (with mocked adapters)
# ═══════════════════════════════════════════════════════════════════════════════

class TestContainer:
    def setup_method(self):
        from src.infrastructure.container import Container
        Container.reset()
        self.container = Container.get_instance()

    def test_singleton(self):
        from src.infrastructure.container import Container
        c1 = Container.get_instance()
        c2 = Container.get_instance()
        assert c1 is c2

    def test_lazy_cache(self):
        c = self.container.cache
        assert c is not None

    def test_lazy_event_bus(self):
        bus = self.container.event_bus
        assert bus is not None

    def test_injection_user_repo(self):
        from src.domain.interfaces import IUserRepository
        class MockUserRepo(IUserRepository):
            def find_by_id(self, user_id): return None
            def find_by_email(self, email): return None
            def save_user(self, user): pass
            def get_session(self): return None
            def save_session(self, data): pass
            def clear_session(self): pass
            def get_token(self): return None
            def get_user(self, user_id): return None

        mock = MockUserRepo()
        self.container.set_user_repo(mock)
        assert self.container.user_repo is mock

    def test_injection_cache(self):
        from src.domain.interfaces import ICacheProvider
        class MockCache(ICacheProvider):
            def get(self, key): return None
            def set(self, key, value, ttl=300): pass
            def delete(self, key): pass
            def clear(self, prefix=""): pass

        mock = MockCache()
        self.container.set_cache(mock)
        assert self.container.cache is mock

    def test_injection_event_bus(self):
        from src.domain.interfaces import IEventBus
        class MockBus(IEventBus):
            def publish(self, event, data=None): pass
            def subscribe(self, event, callback): pass
            def unsubscribe(self, event, callback): pass

        mock = MockBus()
        self.container.set_event_bus(mock)
        assert self.container.event_bus is mock

    def test_reset_clears(self):
        from src.infrastructure.container import Container
        # Inject mock to verify it gets cleared
        from src.domain.interfaces import ICacheProvider
        class MockCache(ICacheProvider):
            def get(self, key): return None
            def set(self, key, value, ttl=300): pass
            def delete(self, key): pass
            def clear(self, prefix=""): pass

        self.container.set_cache(MockCache())
        assert self.container._cache is not None
        Container.reset()
        c2 = Container.get_instance()
        assert c2._cache is None


# ═══════════════════════════════════════════════════════════════════════════════
# Domain Entities
# ═══════════════════════════════════════════════════════════════════════════════

class TestDomainEntities:
    def test_user_entity(self):
        from src.domain.entities import User
        u = User(id="u1", email="a@b.com")
        assert u.id == "u1"
        assert u.plan.value == "gratis"

    def test_user_is_pro(self):
        from src.domain.entities import User, PlanType
        u = User(id="u1", plan=PlanType.PRO)
        assert u.is_pro
        u2 = User(id="u2", plan=PlanType.GRATIS)
        assert not u2.is_pro

    def test_task_entity(self):
        from src.domain.entities import Task
        t = Task(id="t1", user_id="u1", tool_name="minerador", tool_display_name="Minerador")
        assert t.status.value == "pending"
        assert t.progress_percent == 0

    def test_task_is_active(self):
        from src.domain.entities import Task, TaskStatus
        t = Task(id="t1", user_id="u1", tool_name="m", tool_display_name="M", status=TaskStatus.RUNNING)
        assert t.is_active
        t.status = TaskStatus.COMPLETED
        assert not t.is_active

    def test_execution_entity(self):
        from src.domain.entities import Execution
        e = Execution(id=1, user_id="u1", tool_name="minerador")
        assert e.rows_processed == 0
        assert e.status == "completed"

    def test_tool_metadata(self):
        from src.domain.entities import ToolMetadata
        m = ToolMetadata(key="test", name="Test Tool")
        assert m.version == "1.0.0"
        assert m.enabled
        assert m.min_plan.value == "gratis"

    def test_sync_queue_item(self):
        from src.domain.entities import SyncQueueItem
        s = SyncQueueItem(id=1, operation="insert", table_name="execucoes", data_json="{}")
        assert s.status.value == "pending"
        assert s.retry_count == 0

    def test_feature_flag_entity(self):
        from src.domain.entities import FeatureFlagEntity
        f = FeatureFlagEntity(key="flag1", enabled=True, min_plan="pro")
        assert f.enabled
        assert f.rollout_percent == 100


# ═══════════════════════════════════════════════════════════════════════════════
# Application Services
# ═══════════════════════════════════════════════════════════════════════════════

class TestApplicationServices:
    def test_submit_task_use_case(self):
        from src.application.services import SubmitTaskUseCase
        from src.domain.entities import Task

        class FakeTaskRepo:
            def get_task(self, tid): return None
            def save_task(self, task): pass
            def update_task(self, tid, data): pass
            def get_all_tasks(self, sf=None, limit=100): return []
            def get_last_task_by_tool(self, tn): return None
            def get_running_task_by_tool(self, tn): return None
            def delete_task(self, tid): pass

        class FakeUserRepo:
            def get_user(self, uid): return None
            def save_user(self, user): pass
            def get_session(self): return None
            def save_session(self, data): pass
            def clear_session(self): pass
            def get_token(self): return None

        class FakeEventBus:
            def publish(self, event, data=None): pass
            def subscribe(self, event, cb): pass
            def unsubscribe(self, event, cb): pass

        use_case = SubmitTaskUseCase(FakeTaskRepo(), FakeUserRepo(), FakeEventBus())
        task_id, error = use_case.execute("minerador", "Minerador de Preços", {"file": "test.xlsx"}, user_id="u1")
        assert task_id is not None
        assert error is None

    def test_get_user_stats_use_case(self):
        from src.application.services import GetUserStatsUseCase

        class FakeExecRepo:
            def get_executions(self, uid, limit=100):
                return [
                    {"tool_name": "minerador", "rows_processed": 100, "hours_saved": 2.0},
                    {"tool_name": "minerador", "rows_processed": 50, "hours_saved": 1.0},
                ]

        class FakeCache:
            def __init__(self): self._data = {}
            def get(self, key): return self._data.get(key)
            def set(self, key, value, ttl=300): self._data[key] = value
            def delete(self, key): self._data.pop(key, None)
            def clear(self, prefix=""): pass

        cache = FakeCache()
        use_case = GetUserStatsUseCase(FakeExecRepo(), cache)
        stats = use_case.execute("u1")
        assert stats["total_lines"] == 150
        assert stats["total_hours"] == 3.0
        assert stats["total_executions"] == 2

    def test_get_user_stats_uses_cache(self):
        from src.application.services import GetUserStatsUseCase

        class FakeExecRepo:
            def get_executions(self, uid, limit=100):
                return [{"tool_name": "t", "rows_processed": 10, "hours_saved": 0.5}]

        class FakeCache:
            def __init__(self): self._data = {}
            def get(self, key): return self._data.get(key)
            def set(self, key, value, ttl=300): self._data[key] = value
            def delete(self, key): self._data.pop(key, None)
            def clear(self, prefix=""): pass

        cache = FakeCache()
        use_case = GetUserStatsUseCase(FakeExecRepo(), cache)
        stats1 = use_case.execute("u1")
        stats2 = use_case.execute("u1")
        assert stats1 is stats2  # Same cached object


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
