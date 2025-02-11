from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel, Field

from uglychain import llm, react

# from uglychain.schema import T
from uglychain.tool import MCP, Tool, Tools
from uglychain.utils import convert_to_variable_name

from .node import BaseNode


class TaskResponse(BaseModel):
    result: str = Field(description="The final response of the task.")
    context: dict[str, Any] = Field(
        description="Extract the core information and express it concisely using the k:v format."
    )


T = TypeVar("T", bound=TaskResponse)


@dataclass
class Task(BaseNode, Generic[T]):
    description: str
    tools: list[MCP | Tool | Tools] = field(default_factory=list)
    reflection: bool = False
    response_format: type[T] = field(default=TaskResponse)  # type: ignore
    _context: dict[str, Any] = field(init=False)
    _class_context: ClassVar[dict[str, Any]]
    _lock: ClassVar[threading.Lock] = field(default=threading.Lock())

    def __post_init__(self) -> None:
        if hasattr(self, "_class_context"):
            self._context = self._class_context
        else:
            self._context = {}

    def __setitem__(self, key: str, value: Any) -> None:
        if hasattr(self, "_class_context") and self._context is self._class_context:
            with self._lock:
                self._context[convert_to_variable_name(key)] = value
        else:
            self._context[convert_to_variable_name(key)] = value

    def __getitem__(self, key: str) -> Any:
        return self._context[convert_to_variable_name(key)]

    def update(self, context: dict[str, Any]) -> None:
        if hasattr(self, "_class_context") and self._context is self._class_context:
            with self._lock:
                self._context.update(context)
        else:
            self._context.update(context)

    def __hash__(self) -> int:
        return hash((self.description, "".join([tool.name for tool in self.tools]), self.reflection))

    @classmethod
    def set_context(cls, context: dict[str, Any]) -> None:
        cls._class_context = context

    @classmethod
    def delete_context(cls) -> None:
        del cls._class_context

    @property
    def context(self) -> str:
        str = ""
        for key in self._context.keys():
            str += f"<{key}>\n{self._context[key]!r}\n</{key}>\n"
        return str

    @staticmethod
    @llm(need_retry=True)
    def _reflect(context: str, task: str, result: Any) -> None:
        """Reflect on the result of the task. Give advice on how to improve the task."""
        pass

    def _prep(self) -> None:
        pass

    def _exec(self) -> T:
        @react(tools=self.tools, response_format=self.response_format)
        def execute_task(context: str, task: str) -> None:
            return

        return execute_task(self.context, self.description)

    def _post(self, response: T) -> None:
        self.update(response.context)
        self[self.description] = response.result

    def run(self) -> str:
        super().run()
        self._prep()
        response = self._exec()
        self._post(response)

        if self.reflection:
            advice = self._reflect(self.context, self.description, response.result)
            self["Improvement Advice"] = advice
            response = self._exec()
            self._post(response)

        return response.result
