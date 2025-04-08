from __future__ import annotations

import asyncio
import atexit
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from uglychain.utils import singleton

from ..utils import McpTool


def cleanup() -> None:
    ToolsManager().stop()


atexit.register(cleanup)


@singleton
@dataclass
class ToolsManager:
    tools: dict[str, Callable] = field(default_factory=dict)
    mcp_tools: dict[str, McpTool] = field(default_factory=dict)
    mcp_names: set[str] = field(default_factory=set)

    def stop(self) -> None:
        client_names, clients = set(), []
        for tool in self.mcp_tools.values():
            if tool.client.name not in client_names:
                clients.append(tool.client)
                client_names.add(tool.client.name)
        for client in clients:
            asyncio.run(client.close())

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str | tuple[str, str]:
        if tool_name not in self.tools and tool_name not in self.mcp_tools:
            raise ValueError(f"Can't find tool {tool_name}")
        tool = self.tools.get(tool_name)
        if tool:
            return tool(**arguments)
        else:
            mcp_tool = self.mcp_tools.get(tool_name)
            if not mcp_tool:
                raise ValueError(f"Can't find tool {tool_name}")
            return mcp_tool(**arguments)

    def register_tool(self, name: str, func: Callable) -> None:
        if name in self.tools:
            raise ValueError(f"Tool {name} already exists")
        self.tools[name] = func

    def register_mcp(self, name: str) -> None:
        if name in self.mcp_names:
            raise ValueError(f"MCP client {name} already exists")
        self.mcp_names.add(name)

    def register_mcp_tool(self, name: str, tool: McpTool) -> None:
        if name in self.mcp_tools:
            raise ValueError(f"MCP tool {name} already exists")
        self.mcp_tools[name] = tool
