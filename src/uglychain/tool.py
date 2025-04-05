from __future__ import annotations

import asyncio
import atexit
import json
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import cached_property, singledispatch
from typing import Any, ClassVar, cast, overload

from mcp import StdioServerParameters

from .mcp import McpClient, McpTool
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
    _instance: ClassVar[ToolsManager | None] = None

    def __post_init__(self) -> None:
        self.start()

    @classmethod
    def get(cls) -> ToolsManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._executor = ThreadPoolExecutor().__enter__()

    def stop(self) -> None:
        client_names, clients = set(), []
        for tool in self.mcp_tools.values():
            if tool.client.name not in client_names:
                clients.append(tool.client)
                client_names.add(tool.client.name)
        for client in clients:
            asyncio.run(client.close())
        if self._executor:
            self._executor.__exit__(None, None, None)
        self._loop.stop()

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str | tuple[str, str]:
        tool = self.tools.get(tool_name)
        if tool:
            return tool(**arguments)
        else:
            mcp_tool = self.mcp_tools.get(tool_name)
            if not mcp_tool:
                raise ValueError(f"Can't find tool {tool_name}")
            future = self._executor.submit(self._loop.run_until_complete, mcp_tool._arun(**arguments))
            return future.result()

    def register_tool(self, name: str, func: Callable) -> None:
        if name in self.tools:
            raise ValueError(f"Tool {name} already exists")
        self.tools[name] = func

    def register_mcp(self, name: str, mcp: MCP) -> McpClient:
        if name in {name.split(":")[0] for name in self.mcp_tools.keys()}:
            raise ValueError(f"MCP client {name} already exists")
        client = McpClient(name, StdioServerParameters(command=mcp.command, args=mcp.args, env=mcp.env or {}))
        self.mcp_tools[name] = McpTool(client_name=name, name=name, description="", args_schema={}, client=client)
        return client

    def activate_mcp_client(self, client: McpClient) -> None:
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

    def __call__(self, **arguments: Any) -> str | tuple[str, ...]:
        if self.name not in self._manager.tools:
            raise ValueError(f"Tool {self.name} not registered")
        return self._manager.call_tool(self.name, arguments)

    @classmethod
    def call_tool(cls, tool_name: str, **arguments: Any) -> str | tuple[str, str]:
        if tool_name not in cls._manager.tools and tool_name not in cls._manager.mcp_tools:
            raise ValueError(f"Can't find tool {tool_name}")
        return cls._manager.call_tool(tool_name, arguments)

    @overload
    @classmethod
    def tool(cls, obj: type[Any]) -> Tools: ...  # type: ignore
    @overload
    @classmethod
    def tool(cls, obj: object) -> Tool: ...
    @classmethod
    def tool(cls, obj: type[Any] | object) -> Tool | Tools:
        return tool_wrapper(obj, cls)

    @classmethod
    def mcp(cls, obj: type) -> MCP:
        mcp = MCP(command=getattr(obj, "command", ""), args=getattr(obj, "args", []), env=getattr(obj, "env", {}))
        mcp._client = cls._manager.register_mcp(obj.__name__, mcp)
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
        config = {k: v for k, v in config_dict.items() if k in {"command", "args", "env", "disabled", "autoApprove"}}
        mcp = MCP(**config)
        mcp._client = cls._manager.register_mcp(name, mcp)
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
            self.env[key] = os.getenv(key, self.env[key])
        self.env["PATH"] = os.getenv("PATH", "")

    @cached_property
    def tools(self) -> list[Tool]:
        if self.disabled:
            return []
        if self._client._session is None:
            Tool.activate_mcp_client(self._client)
        return [
            Tool(name=f"{self._client.name}:{tool.name}", description=tool.description, args_schema=tool.args_schema)
            for tool in self._client.tools
        ]

    @cached_property
    def name(self) -> str:
        if self._client._session is None:
            Tool.activate_mcp_client(self._client)
        return self._client.name


@singledispatch
def tool_wrapper(obj: Any, cls: type[Tool]) -> Tool | Tools:
    raise NotImplementedError("Method not implemented for this type")


@tool_wrapper.register(object)
def _(func: Callable, cls: type[Tool]) -> Tool:
    name = func.__name__
    if name in cls._manager.tools:
        raise ValueError(f"Tool {name} already exists")
    cls._manager.register_tool(name, func)
    schema = function_schema(func)
    return cls(name=name, description=schema["description"], args_schema=schema["parameters"])


class Tools:
    name: str
    tools: list[Tool]

    def __getattr__(self, name: str) -> Any:
        return getattr(self, name)


@tool_wrapper.register(type)
def _(obj: type, cls: type[Tool]) -> Tools:
    if hasattr(obj, "tools"):
        delattr(obj, "tools")
    new_obj = cast(Tools, obj)
    new_obj.tools = []
    new_obj.name = obj.__name__
    for _name in dir(obj):
        method = getattr(obj, _name)
        if _name.startswith("_") or not callable(method):
            continue
        name = f"{new_obj.name}:{_name}"
        if name in cls._manager.tools:
            raise ValueError(f"Tool {name} already exists")
        # method.__name__ = name
        cls._manager.register_tool(name, method)
        schema = function_schema(method)
        new_obj.tools.append(cls(name=name, description=schema["description"], args_schema=schema["parameters"]))  # type: ignore
    return new_obj


def convert_to_tools(tools: list[Tool | MCP | Tools] | None) -> list[Tool]:
    return [tool for t in tools or [] for tool in ([t] if isinstance(t, Tool) else t.tools)]
