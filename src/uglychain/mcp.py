from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from pydantic_core import to_json


@dataclass
class McpTool:
    client_name: str
    name: str
    description: str
    args_schema: dict[str, Any]
    client: McpClient

    async def _arun(self, **kwargs: Any) -> str:
        result = await self.client._session.call_tool(self.name, arguments=kwargs)  # type: ignore
        return to_json(result.content).decode()


@dataclass
class McpClient:
    name: str
    server_param: StdioServerParameters
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

    async def initialize(self, force_refresh: bool = False) -> None:
        if self._tools and not force_refresh:
            return

        try:
            await self._start_session()
            tools: types.ListToolsResult = await self._session.list_tools()  # type: ignore
            self._tools.extend(
                McpTool(self.name, tool.name, tool.description or "", tool.inputSchema, self) for tool in tools.tools
            )
        except Exception as e:
            print(f"Error gathering tools for {self.server_param.command} {' '.join(self.server_param.args)}: {e}")
            raise

    async def close(self) -> None:
        pass
        """
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
        """

    @property
    def tools(self) -> list[McpTool]:
        return self._tools
