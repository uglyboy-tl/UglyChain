from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aisuite.utils.tools import Tools


def function_schema(func: Callable) -> dict[str, Any]:
    tool = Tools()
    tool._add_tool(func)
    spec = tool.tools()[0]
    return spec.get("function")
