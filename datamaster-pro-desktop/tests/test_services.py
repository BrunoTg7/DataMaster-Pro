"""
Tests for Application Services layer
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestToolService:
    """Tests for ToolService."""

    def test_import(self):
        from src.core.services.tool_service import ToolService
        assert ToolService is not None

    def test_submit_delegates(self):
        from src.core.services.tool_service import ToolService
        svc = ToolService()
        mock_executor = MagicMock()
        mock_executor.submit.return_value = ("task-123", None)
        svc._executor = mock_executor

        task_id, err = svc.submit("tool", "Tool", lambda: {}, None, "user-1")
        assert task_id == "task-123"
        assert err is None
        mock_executor.submit.assert_called_once()

    def test_create_task_delegates(self):
        from src.core.services.tool_service import ToolService
        svc = ToolService()
        mock_executor = MagicMock()
        mock_executor.create_task.return_value = ("task-456", None)
        svc._executor = mock_executor

        task_id, err = svc.create_task("tool", {"key": "val"})
        assert task_id == "task-456"
        mock_executor.create_task.assert_called_once()

    def test_cancel_returns_bool(self):
        from src.core.services.tool_service import ToolService
        svc = ToolService()
        mock_executor = MagicMock()
        mock_executor.cancel_task.return_value = True
        svc._executor = mock_executor

        result = svc.cancel_task("task-1")
        assert result is True

    def test_get_tasks_delegates(self):
        from src.core.services.tool_service import ToolService
        svc = ToolService()
        mock_executor = MagicMock()
        mock_executor.get_tasks.return_value = [{"id": "t1"}]
        svc._executor = mock_executor

        tasks = svc.get_tasks()
        assert len(tasks) == 1


class TestUserService:
    """Tests for UserService."""

    def test_import(self):
        from src.core.services.user_service import UserService
        assert UserService is not None

    def test_logout_calls_both(self):
        from src.core.services.user_service import UserService
        svc = UserService()
        svc._auth = MagicMock()
        svc._storage = MagicMock()
        svc.logout()
        svc._auth.logout.assert_called_once()
        svc._storage.clear_session.assert_called_once()

    def test_get_current_user(self):
        from src.core.services.user_service import UserService
        svc = UserService()
        svc._auth = MagicMock()
        svc._auth.get_current_user.return_value = {"id": "u1"}
        user = svc.get_current_user()
        assert user["id"] == "u1"


class TestIToolInterface:
    """Tests for ITool interface and auto-registration."""

    def test_import_itool(self):
        from src.tools.itool import ITool, register_tool
        assert ITool is not None
        assert register_tool is not None

    def test_register_tool_decorator(self):
        from src.tools.itool import register_tool, _TOOL_REGISTRY
        _TOOL_REGISTRY.pop("_test_tool_dummy", None)

        @register_tool("_test_tool_dummy", "Test Tool")
        class DummyTool:
            pass

        assert "_test_tool_dummy" in _TOOL_REGISTRY
        assert _TOOL_REGISTRY["_test_tool_dummy"] is DummyTool
        assert DummyTool.TOOL_KEY == "_test_tool_dummy"
        assert DummyTool.TOOL_NAME == "Test Tool"

        del _TOOL_REGISTRY["_test_tool_dummy"]

    def test_register_tool_with_page_module(self):
        from src.tools.itool import register_tool, _TOOL_REGISTRY, _TOOL_PAGE_MAP
        _TOOL_REGISTRY.pop("_test_tool_page", None)
        _TOOL_PAGE_MAP.pop("_test_tool_page", None)

        @register_tool("_test_tool_page", "Test Page Tool",
                        "src.gui.pages.tools.test_page")
        class DummyPageTool:
            pass

        assert "_test_tool_page" in _TOOL_PAGE_MAP
        assert _TOOL_PAGE_MAP["_test_tool_page"] == "src.gui.pages.tools.test_page"
        assert DummyPageTool.TOOL_PAGE_MODULE == "src.gui.pages.tools.test_page"

        del _TOOL_REGISTRY["_test_tool_page"]
        del _TOOL_PAGE_MAP["_test_tool_page"]

    def test_get_all_tools(self):
        # Import tool_registry to trigger legacy registration
        from src.tools.tool_registry import TOOL_REGISTRY
        from src.tools.itool import get_all_tools
        tools = get_all_tools()
        assert isinstance(tools, dict)
        assert len(tools) >= 16

    def test_get_tool_page_map(self):
        from src.tools.tool_registry import TOOL_PAGE_MODULES
        from src.tools.itool import get_tool_page_map
        pages = get_tool_page_map()
        assert isinstance(pages, dict)
        assert len(pages) >= 15

    def test_get_tool_class(self):
        from src.tools.tool_registry import TOOL_REGISTRY
        from src.tools.itool import get_tool_class
        cls = get_tool_class("minerador")
        assert cls is not None

    def test_get_tool_class_missing(self):
        from src.tools.itool import get_tool_class
        cls = get_tool_class("nonexistent_tool_xyz")
        assert cls is None


class TestToastComponent:
    """Tests for Toast component."""

    def test_import(self):
        from src.gui.components.toast import Toast, ToastManager
        assert Toast is not None
        assert ToastManager is not None


class TestServiceSingletons:
    """Tests for service singleton accessors."""

    def test_get_tool_service(self):
        from src.core.services import get_tool_service
        svc = get_tool_service()
        assert svc is not None
        svc2 = get_tool_service()
        assert svc is svc2

    def test_get_user_service(self):
        from src.core.services import get_user_service
        svc = get_user_service()
        assert svc is not None
        svc2 = get_user_service()
        assert svc is svc2
