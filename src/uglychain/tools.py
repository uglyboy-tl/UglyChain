from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


def function_schema(func: Callable) -> dict[str, Any]:
    signature = inspect.signature(func)
    docstring = inspect.getdoc(func)
    parameters: dict[str, Any] = {}
    required: list[str] = []
    for param in signature.parameters.values():
        name = param.name
        if name != "self" and param.default == inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": docstring if docstring else "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }


def add_tools_to_parameters(params: dict[str, Any], tools: list[Callable] | None) -> None:
    if tools is None or not tools:
        return
    params["tools"] = []
    for tool in tools:
        params["tools"].append(function_schema(tool))
    if len(tools) == 1:
        params["tool_choice"] = {"type": "function", "function": {"name": tools[0].__name__}}
