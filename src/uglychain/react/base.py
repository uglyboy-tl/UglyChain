from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Generic

from uglychain.schema import Messages, T
from uglychain.session import Session
from uglychain.tools import BaseTool

from .action import Action


@dataclass
class BaseReActProcess(Generic[T], ABC):
    func: Callable[..., str | Messages | None] = field(init=False)
    model: str
    session: Session
    tools: list[BaseTool]
    response_format: type[T] | None
    api_params: dict[str, Any]

    @cached_property
    @abstractmethod
    def react(self) -> Callable[..., Action]:
        pass

    @cached_property
    @abstractmethod
    def final(self) -> Callable[..., str | Iterator[str] | T]:
        pass

    @cached_property
    def tools_descriptions(self) -> str:
        descriptions = []

        for tool in self.tools:
            markdown = f"### {tool.name}\n"
            markdown += f"> {tool.description}\n\n"
            markdown += f"{json.dumps(tool.args_schema, ensure_ascii=False)}\n"
            descriptions.append(markdown)
        return "\n".join(descriptions)
