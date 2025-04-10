from __future__ import annotations

from unittest.mock import MagicMock

from uglychain.tools.core import Tool
from uglychain.tools.core.tool_manager import ToolsManager, cleanup


def test_call_tool_with_console():
    Tool._manager = ToolsManager()
    Tool._manager.tools["test_tool"] = MagicMock(return_value="result")
    result = Tool.call_tool("test_tool", arg1="value1")
    assert result == "result"


def test_tools_manager_singleton():
    instance1 = ToolsManager()
    instance2 = ToolsManager()
    assert instance1 is instance2


def test_cleanup(mocker):
    mock_stop = mocker.patch.object(ToolsManager(), "cleanup_clients")
    cleanup()
    mock_stop.assert_called_once()

    Tool._manager = ToolsManager()

    @Tool.tool
    def sample_tool1():
        pass

    assert "sample_tool1" in Tool._manager.tools
