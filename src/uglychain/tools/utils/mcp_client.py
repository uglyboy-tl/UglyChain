from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Annotated, Any, ClassVar

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from pydantic.networks import AnyUrl, UrlConstraints


@dataclass
class McpTool:
    client_name: str
    client: McpClient
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)

    async def _arun(self, **kwargs: Any) -> str:
        if not self.client._session:
            self.client.initialize()
        result = await self.client.session.call_tool(self.name, arguments=kwargs)
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
class McpResource:
    client_name: str
    client: McpClient
    name: str
    uri: Annotated[AnyUrl, UrlConstraints(host_required=False)] | str
    description: str = ""
    mime_type: str = ""

    async def _aread(self, uri: AnyUrl | None = None) -> list[str]:
        if not self.client._session:
            self.client.initialize()
        if uri is None:
            if isinstance(self.uri, AnyUrl):
                uri = self.uri
            else:
                raise ValueError("URI is not set")
        response = await self.client.session.read_resource(uri)
        result = []
        for content in response.contents:
            if isinstance(content, types.TextResourceContents):
                result.append(content.text)
            elif isinstance(content, types.BlobResourceContents):
                result.append(content.blob)
            else:
                raise ValueError(f"Unsupported content type: {type(content)}")
        return result

    def __call__(self, uri: AnyUrl | None = None) -> list[str]:
        future = self.client._executor.submit(self.client._loop.run_until_complete, self._aread(uri))
        return future.result()


@dataclass
class McpClient:
    name: str
    server_param: StdioServerParameters | dict[str, Any] | str
    use_resources: bool = False
    session: ClientSession = field(init=False)
    _session: ClientSession | None = None
    _client: Any = field(init=False, default=None)
    _tools: list[McpTool] = field(init=False, default_factory=list)
    _resources: list[McpResource] = field(init=False, default_factory=list)
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

    @classmethod
    def create_sse(
        cls,
        name: str,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: float = 5,
        sse_read_timeout: float = 60 * 5,
    ) -> McpClient:
        return cls(
            name, {"url": url, "headers": headers or {}, "timeout": timeout, "sse_read_timeout": sse_read_timeout}
        )

    @classmethod
    def create_websocket(cls, name: str, url: str) -> McpClient:
        return cls(name, url)

    async def _start_session(self) -> ClientSession:
        async with self._init_lock:
            try:
                if self._session is None:
                    if isinstance(self.server_param, StdioServerParameters):
                        self._client = stdio_client(self.server_param)
                    elif isinstance(self.server_param, dict):
                        self._client = sse_client(**self.server_param)
                    elif isinstance(self.server_param, str):
                        try:
                            from mcp.client.websocket import websocket_client

                            self._client = websocket_client(self.server_param)
                        except ImportError as err:
                            raise ImportError(
                                "WebSocket client is not available. Please install the required package."
                            ) from err
                    else:
                        raise ValueError(f"Unsupported server parameters type: {type(self.server_param)}")
                    read, write = await self.exit_stack.enter_async_context(self._client)
                    _session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                    await _session.initialize()
                    self._session = _session
            except Exception as e:
                print(f"Error starting session for {self.name}: {e}")
                await self.close()
                raise
            return self._session

    async def _ainitialize(self, force_refresh: bool) -> None:
        if self._tools and not force_refresh:
            return

        self.session = await self._start_session()
        try:
            tools: types.ListToolsResult = await self.session.list_tools()
            self._tools.extend(
                McpTool(self.name, self, tool.name, tool.description or "", tool.inputSchema) for tool in tools.tools
            )
        except Exception as e:
            if isinstance(self.server_param, StdioServerParameters):
                print(f"Error gathering tools for {self.server_param.command} {' '.join(self.server_param.args)}: {e}")
            else:
                print(f"Error gathering tools for {self.server_param}: {e}")
            raise

        if not self.use_resources:
            return
        try:
            resources: types.ListResourcesResult = await self.session.list_resources()
            self._resources.extend(
                McpResource(
                    self.name, self, resource.name, resource.uri, resource.description or "", resource.mimeType or ""
                )
                for resource in resources.resources
            )
            resources_templates: types.ListResourceTemplatesResult = await self.session.list_resource_templates()
            self._resources.extend(
                McpResource(
                    self.name,
                    self,
                    template.name,
                    template.uriTemplate,
                    template.description or "",
                    template.mimeType or "",
                )
                for template in resources_templates.resourceTemplates
            )
        except Exception as e:
            if isinstance(self.server_param, StdioServerParameters):
                print(
                    f"Error gathering resources for {self.server_param.command} {' '.join(self.server_param.args)}: {e}"
                )
            else:
                print(f"Error gathering resources for {self.server_param}: {e}")
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
                del self.session
                self._client = None
            except Exception as e:
                print(f"Error during cleanup of server {self.name}: {e}")

    @property
    def tools(self) -> list[McpTool]:
        return self._tools
