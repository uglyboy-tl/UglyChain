from __future__ import annotations

from .base import BaseTool, ToolsClass
from .mcp import MCP
from .tool import Tool

Tools = list[Tool | MCP | ToolsClass]


def convert_to_tool_list(tools: Tools | None) -> list[BaseTool]:
    return [tool for t in tools or [] for tool in ([t] if isinstance(t, Tool) else t.tools)]
