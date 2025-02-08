from __future__ import annotations

import asyncio
import atexit
import json
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, ClassVar

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from pydantic_core import to_json

from .console import Console
from .utils import function_schema


def cleanup() -> None:
    ToolsManager.get().stop()


atexit.register(cleanup)


@dataclass
class ToolsManager:
    tools: dict[str, Callable] = field(default_factory=dict)
    mcp_tools: dict[str, McpTool] = field(default_factory=dict)
    _loop: asyncio.AbstractEventLoop = field(init=False)
    _executor: ThreadPoolExecutor = field(init=False)
    _instance: ClassVar[ToolsManager]

    def __post_init__(self) -> None:
        self.start()

    @classmethod
    def get(cls) -> ToolsManager:
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def start(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._executor = ThreadPoolExecutor().__enter__()

    def stop(self) -> None:
        clients = []
        client_names = []
        for tool in self.mcp_tools.values():
            if tool.client.name in client_names:
                continue
            clients.append(tool.client)
            client_names.append(tool.client.name)
        for client in clients:
            asyncio.run(client.close())
        if self._executor:
            self._executor.__exit__(None, None, None)
        if self._loop:
            self._loop.stop()

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        tool = self.tools.get(tool_name, None)
        if tool:
            return tool(**arguments)
        else:
            mcp_tool = self.mcp_tools.get(tool_name)
            if not mcp_tool:
                raise ValueError(f"Can't find tool {tool_name}")
            future = self._executor.submit(self._loop.run_until_complete, mcp_tool._arun(**arguments))
            return future.result()

    def regedit_tool(self, name: str, func: Callable) -> None:
        if name in self.tools:
            raise ValueError(f"Tool {name} already exists")
        self.tools[name] = func

    def regedit_mcp(self, name: str, mcp: MCP) -> McpClient:
        mcp_client_name = set([name.split(":")[0] for name in self.mcp_tools.keys()])
        if name in mcp_client_name:
            raise ValueError(f"MCP client {name} already exists")
        client = McpClient(name, StdioServerParameters(command=mcp.command, args=mcp.args, env=mcp.env or {}))
        self.mcp_tools[name] = McpTool(client_name=name, name=name, description="", args_schema={}, client=client)
        return client

    def activate_mcp_client(self, client: McpClient) -> None:
        if not self._loop.is_running():
            self.start()
        future = self._executor.submit(self._loop.run_until_complete, client.initialize())
        future.result()
        for tool in client.tools:
            self.mcp_tools[f"{client.name}:{tool.name}"] = tool


@dataclass
class Tool:
    name: str
    description: str
    args_schema: dict[str, Any]

    _manager: ClassVar[ToolsManager] = ToolsManager.get()

    def __call__(self, **arguments: Any) -> str:
        if self.name not in self._manager.tools:
            raise ValueError(f"Tool {self.name} not registered")
        return self._manager.call_tool(self.name, arguments)

    @classmethod
    def call_tool(cls, tool_name: str, console: Console | None = None, **arguments: Any) -> str:
        if console is None:
            console = Console()
        if tool_name not in cls._manager.tools and tool_name not in cls._manager.mcp_tools:
            raise ValueError(f"Can't find tool {tool_name}")
        if not console.call_tool_confirm(tool_name, arguments):
            return "User cancelled. Please find other ways to solve this problem."
        return cls._manager.call_tool(tool_name, arguments)

    @classmethod
    def tool(cls, func: Callable) -> Tool:
        name = func.__name__
        if name in cls._manager.tools:
            raise ValueError(f"Tool {name} already exists")
        cls._manager.regedit_tool(name, func)
        schema = function_schema(func)
        return cls(name=func.__name__, description=schema["description"], args_schema=schema["parameters"])

    @classmethod
    def mcp(cls, obj: type) -> MCP:
        command: str = getattr(obj, "command", "")
        args: list[str] = getattr(obj, "args", [])
        env: dict[str, str] = getattr(obj, "env", {})

        mcp = MCP(command, args, env)
        mcp._client = cls._manager.regedit_mcp(obj.__name__, mcp)
        return mcp

    @classmethod
    def load_mcp_config(cls, config_str: str) -> MCP:
        try:
            config_origin = json.loads(f"{{{config_str}}}")
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON format") from e
        assert len(config_origin) == 1
        name, config_dict = list(config_origin.items())[0]
        assert isinstance(config_dict, dict)
        config = {k: v for k, v in config_dict.items() if k in ["command", "args", "env", "disabled", "autoApprove"]}
        mcp = MCP(**config)
        mcp._client = cls._manager.regedit_mcp(name, mcp)
        return mcp

    @classmethod
    def activate_mcp_client(cls, client: McpClient) -> None:
        cls._manager.activate_mcp_client(client)


@dataclass
class MCP:
    command: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    disabled: bool = False
    autoApprove: list[str] = field(default_factory=list)  # noqa: N815
    _client: McpClient = field(init=False)

    def __post_init__(self) -> None:
        for key in self.env:
            self.env[key] = os.getenv(key) or self.env[key]
        self.env["PATH"] = os.getenv("PATH") or ""

    @cached_property
    def tools(self) -> list[Tool]:
        tools: list[Tool] = []
        if self.disabled:
            return tools
        if not hasattr(self, "_client"):
            Tool.activate_mcp_client(self._client)
        for tool in self._client.tools:
            tools.append(
                Tool(
                    name=f"{self._client.name}:{tool.name}",
                    description=tool.description,
                    args_schema=tool.args_schema,
                )
            )
        return tools

    @cached_property
    def name(self) -> str:
        if not hasattr(self, "_client"):
            Tool.activate_mcp_client(self._client)
        return self._client.name


@dataclass
class McpTool:
    client_name: str
    name: str
    description: str
    args_schema: dict[str, Any]
    client: McpClient

    async def _arun(self, **kwargs: Any) -> str:
        result = await self.client._session.call_tool(self.name, arguments=kwargs)  # type: ignore
        content = to_json(result.content).decode()
        return content


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
            for tool in tools.tools:
                self._tools.append(
                    McpTool(
                        self.name,
                        tool.name,
                        tool.description if tool.description else "",
                        tool.inputSchema,
                        self,
                    )
                )
        except Exception as e:
            print(f"Error gathering tools for {self.server_param.command} {' '.join(self.server_param.args)}: {e}")
            raise e

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


def convert_to_tools(tools: list[Tool | MCP] | None) -> list[Tool]:
    _tools: list[Tool] = []
    for tool in tools or []:
        if isinstance(tool, MCP):
            _tools.extend(tool.tools)
        else:
            _tools.append(tool)
    return _tools
