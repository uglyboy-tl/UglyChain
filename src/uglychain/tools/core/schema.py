from __future__ import annotations

from typing import Any

from .base_tool import BaseTool
from .mcp import MCP


class ToolsClass:
    name: str
    tools: list[BaseTool]

    def __getattr__(self, name: str) -> Any:
        return getattr(self, name)


Tools = list[BaseTool | MCP | ToolsClass]


def convert_to_tool_list(tools: Tools | None) -> list[BaseTool]:
    return [tool for t in tools or [] for tool in ([t] if isinstance(t, BaseTool) else t.tools)]
