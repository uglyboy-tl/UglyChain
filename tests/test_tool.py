from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from time import sleep
from unittest.mock import MagicMock

import pytest

from uglychain.tool import MCP, McpClient, McpTool, Tool, ToolsManager


@pytest.fixture
def tools_manager():
    return ToolsManager.get()


class SampleMCP:
    command = "command"
    args = ["arg1"]
    env = {"key": "value"}


def test_initialization(tools_manager):
    assert isinstance(tools_manager, ToolsManager)


def test_start(tools_manager):
    tools_manager.start()
    assert tools_manager._executor is not None


def test_start_and_stop(tools_manager, mocker):
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


def test_call_tool(tools_manager):
    mock_tool = MagicMock(return_value="result")
    tools_manager.tools["test_tool"] = mock_tool
    result = tools_manager.call_tool("test_tool", {"arg1": "value1"})
    assert result == "result"
    mock_tool.assert_called_once_with(arg1="value1")


def test_regedit_tool(tools_manager):
    def sample_tool():
        pass

    tools_manager.regedit_tool("sample_tool", sample_tool)
    assert "sample_tool" in tools_manager.tools

    with pytest.raises(ValueError):
        tools_manager.regedit_tool("sample_tool", sample_tool)


def test_call_tool_with_console(mocker):
    mock_console = mocker.patch("uglychain.tool.Console")
    mock_console.call_tool_confirm.return_value = True
    Tool._manager = ToolsManager()
    Tool._manager.tools["test_tool"] = MagicMock(return_value="result")
    result = Tool.call_tool("test_tool", mock_console, arg1="value1")
    assert result == "result"


def test_tool_decorator():
    Tool._manager = ToolsManager()

    @Tool.tool
    def sample_tool():
        pass

    assert "sample_tool" in Tool._manager.tools


def test_tool_call_tool(tools_manager, mocker):
    mock_console = mocker.patch("uglychain.tool.Console")
    mock_console.call_tool_confirm.side_effect = [True, False]  # Test both confirm and deny
    Tool._manager = tools_manager
    Tool._manager.tools["test_tool"] = MagicMock(return_value="result")
    result = Tool.call_tool("test_tool", mock_console, arg1="value1")
    assert result == "result"
    mock_console.call_tool_confirm.assert_called_once_with("test_tool", {"arg1": "value1"})
    tools_manager.mcp_tools.clear()


def test_tool_validate_call_tool():
    with pytest.raises(ValueError, match="Can't find tool non_existent_tool"):
        Tool.call_tool("non_existent_tool", None)


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


def test_tool_activate_mcp_client(tools_manager, mocker):
    mcp = Tool.mcp(SampleMCP)
    assert isinstance(mcp._client, McpClient)
    mock_initialize = mocker.patch.object(mcp._client, "initialize")
    mocker.patch.object(mcp._client, "_tools", return_value=[])
    tools_manager.activate_mcp_client(mcp._client)
    mock_initialize.assert_called_once()
    assert mcp.tools is not None


def test_mcp(tools_manager):
    class Fetch:  # noqa: N801
        command = "uvx"
        args = ["mcp-server-fetch"]

    fetch = Tool.mcp(Fetch)
    assert fetch.tools[0].name == "Fetch:fetch"
    assert Tool.call_tool("Fetch:fetch", None, url="https://jsonplaceholder.typicode.com/posts")
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


def test_regedit_mcp(tools_manager):
    mcp = SampleMCP()
    client = tools_manager.regedit_mcp("sample_mcp", mcp)
    assert "sample_mcp" in tools_manager.mcp_tools
    assert isinstance(client, McpClient)

    with pytest.raises(ValueError):
        tools_manager.regedit_mcp("sample_mcp", mcp)
