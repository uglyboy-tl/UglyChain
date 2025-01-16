from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Any

import anyio
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from pydantic_core import to_json

DEFAULT_CONFIG = """{
  "mcpServers": {
  }
}"""


@dataclass
class ServerConfig:
    """Configuration for an MCP server."""

    command: str
    args: list[str] | None = None
    env: dict[str, str] | None = None
    enabled: bool = True
    exclude_tools: list[str] | None = None
    requires_confirmation: list[str] | None = None

    @classmethod
    def from_dict(cls, config: dict) -> ServerConfig:
        """Create ServerConfig from dictionary."""
        return cls(
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env", {}),
            enabled=config.get("enabled", True),
            exclude_tools=config.get("exclude_tools", []),
            requires_confirmation=config.get("requires_confirmation", []),
        )


@dataclass
class AppConfig:
    mcp_servers: dict[str, ServerConfig]
    tools_requires_confirmation: list[str]

    @classmethod
    def load(cls, config_str: str = "") -> AppConfig:
        if not config_str:
            config_str = DEFAULT_CONFIG
        config = json.loads(config_str)

        # Extract tools requiring confirmation
        tools_requires_confirmation = []
        for server_config in config["mcpServers"].values():
            tools_requires_confirmation.extend(server_config.get("requires_confirmation", []))

        return cls(
            mcp_servers={
                name: ServerConfig.from_dict(server_config) for name, server_config in config["mcpServers"].items()
            },
            tools_requires_confirmation=tools_requires_confirmation,
        )

    def get_enabled_servers(self) -> dict[str, ServerConfig]:
        """Get only enabled server configurations."""
        return {name: config for name, config in self.mcp_servers.items() if config.enabled}


@dataclass
class McpServerConfig:
    server_name: str
    server_param: StdioServerParameters
    exclude_tools: list[str] = field(default_factory=list)


@dataclass
class McpTool:
    toolkit_name: str
    name: str
    description: str
    args_schema: dict[str, Any]
    session: ClientSession
    client: McpClient

    async def _arun(self, **kwargs):
        if not self.session:
            self.session = await self.client._start_session()

        result = await self.session.call_tool(self.name, arguments=kwargs)  # type: ignore
        content = to_json(result.content).decode()
        return content


@dataclass
class McpClient:
    name: str
    server_param: StdioServerParameters
    exclude_tools: list[str] = field(default_factory=list)
    _session: ClientSession | None = None
    _tools: list[McpTool] = field(default_factory=list)
    _init_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def _start_session(self) -> ClientSession:
        async with self._init_lock:
            if self._session is None:
                self._client = stdio_client(self.server_param)
                read, write = await self._client.__aenter__()
                self._session = ClientSession(read, write)
                await self._session.__aenter__()
                await self._session.initialize()
            return self._session

    async def initialize(self, force_refresh: bool = False):
        if self._tools and not force_refresh:
            return

        try:
            await self._start_session()
            tools: types.ListToolsResult = await self._session.list_tools()  # type: ignore
            for tool in tools.tools:
                if tool.name in self.exclude_tools:
                    continue
                self._tools.append(
                    McpTool(
                        self.name,
                        tool.name,
                        tool.description if tool.description else "",
                        tool.inputSchema,
                        self._session,  # type: ignore
                        self,
                    )
                )
        except Exception as e:
            print(f"Error gathering tools for {self.server_param.command} {' '.join(self.server_param.args)}: {e}")
            raise e

    async def close(self):
        try:
            if self._session:
                await self._session.__aexit__(None, None, None)
        except Exception:
            # Currently above code doesn't really works and not closing the session
            # But it's not a big deal as we are exiting anyway
            # TODO find a way to cleanly close the session
            pass
        try:
            if self._client:
                await self._client.__aexit__(None, None, None)
        except Exception:
            # TODO find a way to cleanly close the client
            pass

    @property
    def tools(self) -> list[McpTool]:
        return self._tools


async def load_tools(app_config: AppConfig, force_refresh: bool = False) -> tuple[list[McpClient], list[McpTool]]:
    server_configs = [
        McpServerConfig(
            server_name=name,
            server_param=StdioServerParameters(
                command=config.command, args=config.args or [], env={**(config.env or {}), **os.environ}
            ),
            exclude_tools=config.exclude_tools or [],
        )
        for name, config in app_config.get_enabled_servers().items()
    ]

    clients: list[McpClient] = []
    tools: list[McpTool] = []

    async def convert_toolkit(server_config: McpServerConfig):
        client = McpClient(server_config.server_name, server_config.server_param, server_config.exclude_tools)
        await client.initialize(force_refresh=force_refresh)
        clients.append(client)
        tools.extend(client.tools)

    async with anyio.create_task_group() as tg:
        for server_param in server_configs:
            tg.start_soon(convert_toolkit, server_param)

    return clients, tools
