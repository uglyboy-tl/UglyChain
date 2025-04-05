from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from uglychain.tool import MCP, McpClient, McpTool, Tool, ToolsManager, cleanup


@pytest.fixture
def tools_manager():
    return ToolsManager.get()


class SampleMCP:
    command = "command"
    args = ["arg1"]
    env = {"key": "value"}


@pytest.mark.parametrize(
    "method, expected",
    [
        ("start", "_executor"),
        ("stop", None),
    ],
)
def test_tools_manager_methods(tools_manager, method, expected, mocker):
    if method == "start":
        tools_manager.start()
        assert tools_manager._executor is not None
    elif method == "stop":
        try:
            tools_manager.start()
            assert tools_manager._executor is not None
            mock_executor = mocker.patch.object(tools_manager, "_executor", wraps=tools_manager._executor)
            mock_loop = mocker.patch.object(tools_manager, "_loop")
            tools_manager.mcp_tools.clear()
            tools_manager.stop()
            mock_executor.__exit__.assert_called_once()
            mock_loop.stop.assert_called_once()
        finally:
            tools_manager.start()  # Ensure start is called again in case of failure


@contextmanager
def temporary_env_var(key, value):
    original_value = os.environ.get(key, None)
    os.environ[key] = value
    try:
        yield
    finally:
        if original_value is None:
            del os.environ[key]
        else:
            os.environ[key] = original_value


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


def test_call_tool_with_console(mocker):
    Tool._manager = ToolsManager()
    Tool._manager.tools["test_tool"] = MagicMock(return_value="result")
    result = Tool.call_tool("test_tool", arg1="value1")
    assert result == "result"


def test_tools_manager_singleton():
    instance1 = ToolsManager.get()
    instance2 = ToolsManager.get()
    assert instance1 is instance2


def test_cleanup(mocker):
    mock_stop = mocker.patch.object(ToolsManager, "stop")
    cleanup()
    mock_stop.assert_called_once()

    Tool._manager = ToolsManager()

    @Tool.tool
    def sample_tool():
        pass

    assert "sample_tool" in Tool._manager.tools


def test_tool_call_tool(tools_manager, mocker):
    Tool._manager = tools_manager
    Tool._manager.tools["test_tool"] = MagicMock(return_value="result")
    result = Tool.call_tool("test_tool", arg1="value1")
    assert result == "result"
    tools_manager.mcp_tools.clear()


def test_tool_validate_call_tool():
    with pytest.raises(ValueError, match="Can't find tool non_existent_tool"):
        Tool.call_tool("non_existent_tool")
    tool = Tool("test", "test", {})
    with pytest.raises(ValueError, match="Tool test not registered"):
        tool()


def test_tool_mcp(tools_manager):
    class SampleMCP:
        command = "command"
        args = ["arg1"]
        env = {"key1": "value", "key2": "value"}

    with temporary_env_var("key1", "test_value"):
        mcp = Tool.mcp(SampleMCP)
        assert isinstance(mcp, MCP)
        assert mcp.command == "command"
        assert mcp.args == ["arg1"]
        assert mcp.env["key1"] == "test_value"
        assert "PATH" in mcp.env
        assert mcp.env["key2"] == "value"

    tools_manager.mcp_tools.clear()


@pytest.mark.parametrize(
    "mcp_config, exception",
    [
        (
            """"obsidian": {
    "command": "command",
    "args": ["arg1"],
    "disabled": true
}""",
            None,
        ),
        ('{"}', ValueError("Invalid JSON format")),
    ],
)
def test_tool_load_mcp_config(mcp_config, exception, tools_manager):
    if exception:
        with pytest.raises(exception.__class__, match=str(exception)):
            Tool.load_mcp_config(mcp_config)
    else:
        mcp = Tool.load_mcp_config(mcp_config)
        assert isinstance(mcp, MCP)
        assert mcp.command == "command"
        assert mcp.args == ["arg1"]
        assert not mcp.tools

    tools_manager.mcp_tools.clear()


def test_tool_activate_mcp_client(tools_manager, mocker):
    mcp = Tool.mcp(SampleMCP)
    assert isinstance(mcp._client, McpClient)
    mock_initialize = mocker.patch.object(mcp._client, "initialize")
    mocker.patch.object(tools_manager, "start")
    mocker.patch.object(mcp._client, "_tools", return_value=[])
    tools_manager.activate_mcp_client(mcp._client)
    mock_initialize.assert_called_once()
    assert mcp.tools is not None


def test_mcp(tools_manager, mocker):
    # Skip this test if uvx is not installed
    pytest.importorskip("uvx", reason="uvx not installed")

    mock_call_tool = mocker.patch("mcp.ClientSession.call_tool")

    class Fetch:  # noqa: N801
        command = "uvx"
        args = ["mcp-server-fetch"]

    fetch = Tool.mcp(Fetch)
    assert fetch.tools[0].name == "Fetch:fetch"
    assert Tool.call_tool("Fetch:fetch", url="https://jsonplaceholder.typicode.com/posts")
    mock_call_tool.assert_called_once()
    tools_manager.stop()


def test_mcp_post_init(mocker):
    mocker.patch("os.getenv", return_value="test_value")
    mcp = MCP(command="command", args=["arg1"], env={"key": "value"})
    assert mcp.env["key"] == "test_value"
    assert "PATH" in mcp.env


@pytest.mark.asyncio
async def test_mcp_tool_arun(mocker, tools_manager):
    mock_client = mocker.patch("uglychain.tool.McpClient")
    client = mock_client.return_value
    mcp_tool = McpTool(client_name="client", name="tool", description="", args_schema={}, client=client)
    mock_session = mocker.patch.object(client, "_session")
    mock_session.call_tool.return_value = asyncio.Future()
    mock_session.call_tool.return_value.set_result(MagicMock(content="result"))
    result = await mcp_tool._arun(arg1="value1")
    assert result == '"result"'
    tools_manager.mcp_tools.clear()


def test_register_mcp(tools_manager):
    mcp = SampleMCP()
    client = tools_manager.register_mcp("sample_mcp", mcp)
    assert "sample_mcp" in tools_manager.mcp_tools
    assert isinstance(client, McpClient)

    with pytest.raises(ValueError):
        tools_manager.register_mcp("sample_mcp", mcp)
