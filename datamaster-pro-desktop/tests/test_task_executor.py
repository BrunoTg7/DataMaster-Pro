"""
Tests for TaskExecutor - Motor unificado de execução de tarefas
"""
import time
import threading
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.tasks.task_executor import TaskExecutor, TaskInfo, TaskStatus


# ═══════════════════════════════════════════════════════════════════════════════
# TaskInfo
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskInfo:
    def test_default_values(self):
        t = TaskInfo("t1", "minerador", "Minerador", "u1")
        assert t.id == "t1"
        assert t.tool_name == "minerador"
        assert t.tool_display_name == "Minerador"
        assert t.user_id == "u1"
        assert t.status == TaskStatus.PENDING
        assert t.progress_percent == 0
        assert t.rows_processed == 0

    def test_cancel_event(self):
        t = TaskInfo("t1", "m", "M")
        assert not t._cancel_event.is_set()
        t._cancel_event.set()
        assert t._cancel_event.is_set()

    def test_log_messages_default(self):
        t = TaskInfo("t1", "m", "M")
        assert t.log_messages == []

    def test_input_params_default(self):
        t = TaskInfo("t1", "m", "M")
        assert t.input_params == "{}"


# ═══════════════════════════════════════════════════════════════════════════════
# TaskStatus
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskStatus:
    def test_status_values(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
        assert TaskStatus.INTERRUPTED == "interrupted"


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Singleton
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorSingleton:
    def test_singleton_same_instance(self):
        TaskExecutor._instance = None
        e1 = TaskExecutor()
        e2 = TaskExecutor()
        assert e1 is e2

    def test_singleton_resets_after_clear(self):
        TaskExecutor._instance = None
        e1 = TaskExecutor()
        TaskExecutor._instance = None
        e2 = TaskExecutor()
        assert e1 is not e2


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Register Tool
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorRegisterTool:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()

    def test_register_tool(self):
        class FakeTool:
            pass
        self.executor.register_tool("fake", FakeTool)
        assert "fake" in self.executor._tool_registry

    def test_register_tool_replaces(self):
        class Tool1:
            pass
        class Tool2:
            pass
        self.executor.register_tool("t", Tool1)
        self.executor.register_tool("t", Tool2)
        assert self.executor._tool_registry["t"] is Tool2


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Submit
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorSubmit:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        self.executor._storage.get_all_tasks.return_value = []

    def test_submit_returns_task_id(self):
        def dummy():
            return {"rows_processed": 10}
        task_id, error = self.executor.submit("tool1", "Tool 1", dummy)
        assert task_id is not None
        assert error is None

    def test_submit_stores_task(self):
        def dummy():
            return {}
        task_id, _ = self.executor.submit("tool1", "Tool 1", dummy)
        assert task_id in self.executor._tasks

    def test_submit_blocks_same_tool(self):
        self.executor._storage.get_saved_session.return_value = {"plan": "pro"}
        def slow():
            time.sleep(1)
            return {}
        self.executor.submit("tool1", "Tool 1", slow)
        time.sleep(0.05)
        _, error = self.executor.submit("tool1", "Tool 1", slow)
        assert error is not None
        assert "tool" in error.lower() or "execu" in error.lower() or "simult" in error.lower()

    def test_submit_calls_on_complete(self):
        result_holder = []
        def dummy():
            return {"rows_processed": 5}
        def on_complete(result):
            result_holder.append(result)

        self.executor.submit("t1", "T1", dummy, on_complete=on_complete)
        time.sleep(0.2)
        assert len(result_holder) == 1
        assert result_holder[0]["rows_processed"] == 5

    def test_submit_handles_exception(self):
        def failing():
            raise ValueError("test error")
        result_holder = []
        def on_complete(result):
            result_holder.append(result)

        task_id, _ = self.executor.submit("t1", "T1", failing, on_complete=on_complete)
        time.sleep(0.2)
        task = self.executor._tasks.get(task_id)
        assert task.status == TaskStatus.FAILED
        assert "test error" in task.error_message

    def test_submit_cancelled_task(self):
        def slow():
            time.sleep(0.5)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        self.executor.cancel_task(task_id)
        time.sleep(0.3)
        task = self.executor._tasks.get(task_id)
        assert task.status == TaskStatus.CANCELLED


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Create Task
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorCreateTask:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_saved_session.return_value = {"id": "u1", "plan": "gratis"}
        self.executor._storage.get_all_tasks.return_value = []

    def test_create_task_returns_id(self):
        task_id, error = self.executor.create_task("minerador", {"file": "test.xlsx"})
        assert task_id is not None
        assert error is None

    def test_create_task_stores_params(self):
        task_id, _ = self.executor.create_task("minerador", {"file": "test.xlsx"})
        task = self.executor._tasks[task_id]
        assert "test.xlsx" in task.input_params

    def test_create_task_blocks_same_tool_running(self):
        self.executor.create_task("minerador", {})
        time.sleep(0.05)
        _, error = self.executor.create_task("minerador", {})
        assert "em execução" in error.lower() or "já está" in error.lower()

    def test_create_task_auto_execute(self):
        class FakeTool:
            def __init__(self, **kwargs): pass
            def execute(self, params):
                return {"rows_processed": 42}
        self.executor.register_tool("fake", FakeTool)
        task_id, _ = self.executor.create_task("fake", {}, auto_execute=True)
        time.sleep(0.3)
        task = self.executor._tasks.get(task_id)
        assert task.status == TaskStatus.COMPLETED


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Progress & Lifecycle
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorProgress:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        self.executor._storage.get_all_tasks.return_value = []

    def test_update_progress(self):
        def slow():
            time.sleep(0.5)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        self.executor.update_progress(task_id, 50, "Halfway")
        task = self.executor._tasks[task_id]
        assert task.progress_percent == 50
        assert task.progress_message == "Halfway"

    def test_update_progress_clamps(self):
        def slow():
            time.sleep(0.5)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        self.executor.update_progress(task_id, 150)
        task = self.executor._tasks[task_id]
        assert task.progress_percent == 100

    def test_add_log(self):
        def slow():
            time.sleep(0.5)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        self.executor.add_log(task_id, "Step 1")
        self.executor.add_log(task_id, "Step 2")
        task = self.executor._tasks[task_id]
        assert len(task.log_messages) == 2

    def test_add_log_limits_messages(self):
        def slow():
            time.sleep(0.5)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        for i in range(120):
            self.executor.add_log(task_id, f"msg {i}")
        task = self.executor._tasks[task_id]
        assert len(task.log_messages) == 100

    def test_complete_task(self):
        def slow():
            time.sleep(0.5)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        self.executor.complete_task(task_id, "/output.xlsx", 100, 2.5)
        task = self.executor._tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        assert task.rows_processed == 100
        assert task.hours_saved == 2.5
        assert task.output_path == "/output.xlsx"

    def test_fail_task(self):
        def slow():
            time.sleep(0.5)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        self.executor.fail_task(task_id, "something broke")
        task = self.executor._tasks[task_id]
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "something broke"


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Cancel
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorCancel:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        self.executor._storage.get_all_tasks.return_value = []

    def test_cancel_running_task(self):
        def slow():
            time.sleep(1)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        result = self.executor.cancel_task(task_id)
        assert result is True
        task = self.executor._tasks[task_id]
        assert task.status == TaskStatus.CANCELLED

    def test_cancel_nonexistent_returns_false(self):
        assert self.executor.cancel_task("nonexistent") is False

    def test_cancel_completed_returns_false(self):
        def fast():
            return {}
        task_id, _ = self.executor.submit("t1", "T1", fast)
        time.sleep(0.3)
        result = self.executor.cancel_task(task_id)
        assert result is False

    def test_is_cancelled(self):
        def slow():
            time.sleep(1)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        assert not self.executor.is_cancelled(task_id)
        self.executor.cancel_task(task_id)
        assert self.executor.is_cancelled(task_id)


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Query
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorQuery:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        self.executor._storage.get_all_tasks.return_value = []

    def test_get_tasks_empty(self):
        tasks = self.executor.get_tasks()
        assert tasks == []

    def test_get_tasks_with_submitted(self):
        def dummy():
            return {}
        self.executor.submit("t1", "T1", dummy)
        time.sleep(0.05)
        tasks = self.executor.get_tasks()
        assert len(tasks) >= 1

    def test_get_tasks_filter(self):
        def dummy():
            return {}
        self.executor.submit("t1", "T1", dummy)
        time.sleep(0.05)
        running = self.executor.get_tasks(status_filter="running")
        assert all(t["status"] == "running" for t in running)

    def test_get_task_by_id(self):
        def dummy():
            return {}
        task_id, _ = self.executor.submit("t1", "T1", dummy)
        time.sleep(0.05)
        task = self.executor.get_task(task_id)
        assert task is not None
        assert task["id"] == task_id

    def test_get_active_tasks(self):
        def slow():
            time.sleep(1)
            return {}
        self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        active = self.executor.get_active_tasks()
        assert len(active) >= 1

    def test_get_running_count(self):
        def slow():
            time.sleep(1)
            return {}
        self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        assert self.executor.get_running_count() >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Callbacks
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorCallbacks:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        self.executor._storage.get_all_tasks.return_value = []

    def test_on_new_task_callback(self):
        called = []
        self.executor.on_new_task(lambda: called.append(True))
        def dummy():
            return {}
        self.executor.submit("t1", "T1", dummy)
        time.sleep(0.05)
        assert len(called) >= 1

    def test_state_change_callback(self):
        called = []
        self.executor.register_state_change_callback(lambda active: called.append(active))
        def slow():
            time.sleep(0.3)
            return {}
        self.executor.submit("t1", "T1", slow)
        time.sleep(0.1)
        self.executor.complete_task(
            list(self.executor._tasks.keys())[0], "", 0, 0
        )
        time.sleep(0.1)
        assert len(called) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Requeue & Restart
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorRequeue:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        self.executor._storage.get_all_tasks.return_value = []

    def test_requeue_cancelled_task(self):
        def slow():
            time.sleep(1)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        self.executor.cancel_task(task_id)
        new_id, error = self.executor.requeue_task(task_id)
        assert new_id is not None
        assert error is None

    def test_requeue_nonexistent(self):
        _, error = self.executor.requeue_task("fake")
        assert "não encontrada" in error

    def test_requeue_running_fails(self):
        def slow():
            time.sleep(1)
            return {}
        task_id, _ = self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        _, error = self.executor.requeue_task(task_id)
        assert "não pode ser reenviada" in error


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Maintenance
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorMaintenance:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        self.executor._storage.get_all_tasks.return_value = []

    def test_clear_completed_tasks(self):
        def fast():
            return {}
        task_id, _ = self.executor.submit("t1", "T1", fast)
        time.sleep(0.3)
        assert len(self.executor._tasks) == 1
        self.executor.clear_completed_tasks()
        assert len(self.executor._tasks) == 0

    def test_clear_old_tasks(self):
        def dummy():
            return {}
        task_id, _ = self.executor.submit("t1", "T1", dummy)
        time.sleep(0.05)
        task = self.executor._tasks[task_id]
        task.completed_at = "2020-01-01T00:00:00"
        self.executor.clear_old_tasks(days=1)
        assert task_id not in self.executor._tasks

    def test_export_tasks_for_web(self):
        def dummy():
            return {}
        self.executor.submit("t1", "T1", dummy, user_id="u1")
        time.sleep(0.05)
        exported = self.executor.export_tasks_for_web(user_id="u1")
        assert len(exported) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# TaskExecutor - Max Concurrent
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutorMaxConcurrent:
    def setup_method(self):
        TaskExecutor._instance = None
        self.executor = TaskExecutor()
        self.executor._storage = MagicMock()
        self.executor._storage.get_all_tasks.return_value = []

    def test_max_concurrent_gratis(self):
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        assert self.executor.max_concurrent == 1

    def test_max_concurrent_pro(self):
        self.executor._storage.get_saved_session.return_value = {"plan": "pro"}
        assert self.executor.max_concurrent == 2

    def test_blocks_when_at_limit(self):
        self.executor._storage.get_saved_session.return_value = {"plan": "gratis"}
        def slow():
            time.sleep(1)
            return {}
        self.executor.submit("t1", "T1", slow)
        time.sleep(0.05)
        _, error = self.executor.submit("t2", "T2", slow)
        assert "simultânea" in error.lower() or "limite" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
