from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property

from ..utils import McpClient, McpTool
from .base_tool import BaseTool

SSE_PROTOCOL_PATTERN = r"^(http|https)://"
WS_PROTOCOL_PATTERN = r"^(ws|wss)://"


@dataclass
class MCP:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    disabled: bool = False
    autoApprove: list[str] = field(default_factory=list)  # noqa: N815
    _client: McpClient = field(init=False)
    register_callback: Callable[[str, McpTool], None] = field(init=False)

    def __post_init__(self) -> None:
        for key in self.env:
            self.env[key] = os.getenv(key, self.env[key])
        self.env["PATH"] = os.getenv("PATH", "")
        if self.is_sse:
            self._client = McpClient.create_sse(self.name, self.command)
        elif self.is_ws:
            self._client = McpClient.create_websocket(self.name, self.command)
        else:
            self._client = McpClient.create(self.name, self.command, self.args, self.env)

    @cached_property
    def is_sse(self) -> bool:
        if re.match(SSE_PROTOCOL_PATTERN, self.command.strip()):
            return True
        return False

    @cached_property
    def is_ws(self) -> bool:
        if re.match(WS_PROTOCOL_PATTERN, self.command.strip()):
            return True
        return False

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
                    args_schema=tool.input_schema,
                )
            )
        return result
