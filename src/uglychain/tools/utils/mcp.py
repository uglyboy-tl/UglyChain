from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any, ClassVar

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
        if not self.client._session:
            self.client.initialize()
        result = await self.client._session.call_tool(self.name, arguments=kwargs)  # type: ignore
        content = result.content[0]
        if isinstance(content, types.TextContent):
            return content.text
        elif isinstance(content, types.ImageContent):
            return content.data
        elif isinstance(content, types.EmbeddedResource) and isinstance(content.resource, types.TextResourceContents):
            return content.resource.text
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")

    def __call__(self, **kwargs: Any) -> str:
        future = self.client._executor.submit(self.client._loop.run_until_complete, self._arun(**kwargs))
        return future.result()


@dataclass
class McpClient:
    name: str
    server_param: StdioServerParameters
    _session: ClientSession | None = None
    _tools: list[McpTool] = field(default_factory=list)
    _init_lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)
    _cleanup_lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)
    exit_stack: AsyncExitStack = field(init=False, default_factory=AsyncExitStack)
    _loop: ClassVar[asyncio.AbstractEventLoop] = field(init=False, default=asyncio.get_event_loop())
    _executor: ClassVar[ThreadPoolExecutor] = field(init=False, default=ThreadPoolExecutor())

    def __post_init__(self) -> None:
        asyncio.set_event_loop(self._loop)

    @classmethod
    def create(cls, name: str, command: str, args: list[str], env: dict[str, str] | None = None) -> McpClient:
        return cls(name, StdioServerParameters(command=command, args=args, env=env or {}))

    async def _start_session(self) -> ClientSession:
        async with self._init_lock:
            if self._session is None:
                self._client = stdio_client(self.server_param)
                read, write = await self.exit_stack.enter_async_context(self._client)
                _session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await _session.initialize()
                self._session = _session
            return self._session

    async def _ainitialize(self, force_refresh: bool) -> None:
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

    def initialize(self, force_refresh: bool = False) -> None:
        future = self._executor.submit(self._loop.run_until_complete, self._ainitialize(force_refresh))
        future.result()

    async def close(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self._session = None
                self._client = None
            except Exception as e:
                print(f"Error during cleanup of server {self.name}: {e}")

    @property
    def tools(self) -> list[McpTool]:
        return self._tools
