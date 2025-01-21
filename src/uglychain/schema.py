from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from pydantic import BaseModel, Field

P = ParamSpec("P")
T = TypeVar("T", bound=BaseModel)
Content = TypeVar("Content", bound=str | dict[str, Any])
Messages = list[dict[str, Content]]


class ToolResponse(BaseModel):
    name: str = Field(..., description="tool name")
    parameters: dict = Field(..., description="tool arguments")

    @classmethod
    def parse(cls, response: Any) -> ToolResponse:
        return cls(name=response.name, parameters=json.loads(response.arguments))

    def run_function(self, tools: list[Callable[..., str]]) -> str:
        for tool in tools:
            if tool.__name__ == self.name:
                return tool(**self.parameters)
        raise ValueError(f"Can't find tool {self.name}")
