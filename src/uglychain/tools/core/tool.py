from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from functools import singledispatch
from typing import Any, ClassVar, cast, overload

from ..utils import function_schema
from .base_tool import BaseTool
from .mcp import MCP
from .schema import ToolsClass
from .tool_manager import ToolsManager


@dataclass
class Tool:
    _manager: ClassVar[ToolsManager] = ToolsManager()

    @classmethod
    def call_tool(cls, tool_name: str, **arguments: Any) -> str | tuple[str, str]:
        return cls._manager.call_tool(tool_name, arguments)

    @overload
    @classmethod
    def tool(cls, obj: type[Any]) -> ToolsClass: ...  # type: ignore
    @overload
    @classmethod
    def tool(cls, obj: object) -> BaseTool: ...
    @classmethod
    def tool(cls, obj: type[Any] | object) -> BaseTool | ToolsClass:
        return tool_wrapper(obj, cls)

    @classmethod
    def mcp(cls, obj: type) -> MCP:
        mcp = MCP(
            obj.__name__,
            command=getattr(obj, "command", ""),
            args=getattr(obj, "args", []),
            env=getattr(obj, "env", {}),
        )
        cls._manager.register_mcp(obj.__name__)
        mcp.register_callback = cls._manager.register_mcp_tool
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
        mcp = MCP(str(name), **config)
        cls._manager.register_mcp(name)
        mcp.register_callback = cls._manager.register_mcp_tool
        return mcp


@singledispatch
def tool_wrapper(obj: Any, cls: type[Tool]) -> BaseTool | ToolsClass:
    raise NotImplementedError("Method not implemented for this type")


@tool_wrapper.register(object)
def _(func: Callable, cls: type[Tool]) -> BaseTool:
    name = func.__name__
    if name in cls._manager.tools:
        raise ValueError(f"Tool {name} already exists")
    cls._manager.register_tool(name, func)
    schema = function_schema(func)
    return BaseTool(name=name, description=schema["description"], args_schema=schema["parameters"])


@tool_wrapper.register(type)
def _(obj: type, cls: type[Tool]) -> ToolsClass:
    if hasattr(obj, "tools"):
        delattr(obj, "tools")
    new_obj = cast(ToolsClass, obj)
    new_obj.tools = []
    new_obj.name = obj.__name__
    for _name in dir(obj):
        method = getattr(obj, _name)
        if _name.startswith("_") or not callable(method):
            continue
        name = f"{new_obj.name}:{_name}"
        if name in cls._manager.tools:
            raise ValueError(f"Tool {name} already exists")
        cls._manager.register_tool(name, method)
        schema = function_schema(method)
        new_obj.tools.append(BaseTool(name=name, description=schema["description"], args_schema=schema["parameters"]))
    return new_obj
