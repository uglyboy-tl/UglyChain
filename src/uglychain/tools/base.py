from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BaseTool:
    name: str
    description: str
    args_schema: dict[str, Any]


class ToolsClass:
    name: str
    tools: list[BaseTool]

    def __getattr__(self, name: str) -> Any:
        return getattr(self, name)
