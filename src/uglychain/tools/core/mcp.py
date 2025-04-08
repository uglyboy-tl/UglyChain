from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property

from ..utils import McpClient, McpTool
from .base_tool import BaseTool


@dataclass
class MCP:
    name: str
    command: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    disabled: bool = False
    autoApprove: list[str] = field(default_factory=list)  # noqa: N815
    _client: McpClient = field(init=False)
    register_callback: Callable[[str, McpTool], None] = field(init=False)

    def __post_init__(self) -> None:
        for key in self.env:
            self.env[key] = os.getenv(key, self.env[key])
        self.env["PATH"] = os.getenv("PATH", "")
        self._client = McpClient.create(self.name, self.command, self.args, self.env)

    @cached_property
    def tools(self) -> list[BaseTool]:
        if self.disabled:
            return []
        if self._client._session is None:
            self._client.initialize()
        result: list[BaseTool] = []
        for tool in self._client.tools:
            name = f"{self._client.name}:{tool.name}"
            self.register_callback(name, tool)
            result.append(
                BaseTool(
                    name,
                    description=tool.description,
                    args_schema=tool.args_schema,
                )
            )
        return result
