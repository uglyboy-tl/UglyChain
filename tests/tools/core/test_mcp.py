from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from mcp import types

from uglychain.tools.core import Tool
from uglychain.tools.core.mcp import MCP
from uglychain.tools.utils import McpClient, McpTool


class SampleMCP:
    command = "command"
    args = ["arg1"]
    env = {"key": "value"}


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


def test_tool_mcp_and_mcp_client(tools_manager, mocker):
    class SampleMCP:
        command = "command"
        args = ["arg1"]
        env = {"key1": "value", "key2": "value"}

    with temporary_env_var("key1", "test_value"):
        tools_manager.mcp_names.clear()
        mcp = Tool.mcp(SampleMCP)
        assert isinstance(mcp, MCP)
        assert mcp.command == "command"
        assert mcp.args == ["arg1"]
        assert mcp.env["key1"] == "test_value"
        assert "PATH" in mcp.env
        assert mcp.env["key2"] == "value"
        assert isinstance(mcp._client, McpClient)
        mocker.patch.object(mcp._client, "_tools", return_value=[])
        assert mcp.tools is not None
        assert Tool._manager.mcp_names == {"SampleMCP"}
        assert Tool._manager.mcp_tools is not None


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
    tools_manager.cleanup_clients()


def test_mcp_see(tools_manager):
    class Amap:
        command = f"https://mcp.amap.com/sse?key={os.getenv('AMAP_MAPS_API_KEY')}"

    amap = Tool.mcp(Amap)
    assert amap.tools[-1].name == "Amap:maps_weather"
    Tool.call_tool("Amap:maps_weather", city="北京")
    tools_manager.cleanup_clients()


def test_mcp_post_init(mocker):
    mocker.patch("os.getenv", return_value="test_value")
    mcp = MCP("test", command="command", args=["arg1"], env={"key": "value"})
    assert mcp.env["key"] == "test_value"
    assert "PATH" in mcp.env


@pytest.mark.asyncio
async def test_mcp_tool_arun(mocker, tools_manager):
    mock_client = mocker.patch("uglychain.tools.core.mcp.McpClient")
    client = mock_client.return_value
    mcp_tool = McpTool(client_name="client", client=client, name="tool")
    mock_session = mocker.patch.object(client, "session")
    mock_session.call_tool.return_value = asyncio.Future()
    content = types.TextContent(type="text", text="result")
    mock_session.call_tool.return_value.set_result(type("Response", (object,), {"content": [content]}))
    result = await mcp_tool._arun(arg1="value1")
    assert result == "result"
    tools_manager.mcp_tools.clear()


def test_register_mcp(tools_manager):
    tools_manager.register_mcp("sample_mcp")
    assert "sample_mcp" in tools_manager.mcp_names

    with pytest.raises(ValueError):
        tools_manager.register_mcp("sample_mcp")
