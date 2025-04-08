from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uglychain.tools.core import Tool


@pytest.mark.parametrize(
    "tool_name, tool_func, args, expected",
    [
        ("test_tool", MagicMock(return_value="result"), {"arg1": "value1"}, "result"),
    ],
)
def test_call_tool(tools_manager, tool_name, tool_func, args, expected):
    tools_manager.tools[tool_name] = tool_func
    result = tools_manager.call_tool(tool_name, args)
    assert result == expected
    tool_func.assert_called_once_with(**args)


def test_call_tool_with_wrong_tool_name(tools_manager):
    with pytest.raises(ValueError, match="Can't find tool non_existent_tool"):
        tools_manager.call_tool("non_existent_tool", None)


@pytest.mark.parametrize(
    "tool_name, tool_func",
    [
        ("sample_tool", lambda: None),
    ],
)
def test_register_tool(tools_manager, tool_name, tool_func):
    tools_manager.register_tool(tool_name, tool_func)
    assert tool_name in tools_manager.tools
    with pytest.raises(ValueError, match="Tool sample_tool already exists"):
        tool_func.__name__ = "sample_tool"
        Tool.tool(tool_func)
    with pytest.raises(ValueError, match="Tool sample_tool already exists"):
        tools_manager.register_tool(tool_name, tool_func)


def test_tool_call_tool(tools_manager, mocker):
    Tool._manager = tools_manager
    Tool._manager.tools["test_tool"] = MagicMock(return_value="result")
    result = Tool.call_tool("test_tool", arg1="value1")
    assert result == "result"
    tools_manager.mcp_tools.clear()


def test_tool_validate_call_tool():
    with pytest.raises(ValueError, match="Can't find tool non_existent_tool"):
        Tool.call_tool("non_existent_tool")
