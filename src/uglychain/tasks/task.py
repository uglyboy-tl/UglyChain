from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic

from pydantic import BaseModel, Field

from uglychain import llm, react
from uglychain.schema import T
from uglychain.tool import MCP, Tool


class TaskResult(BaseModel):
    response: str = Field(description="The response of the task.")
    steps: str = Field(description="Key steps to solve the task.")


@dataclass
class Task(Generic[T]):
    description: str
    response_format: type[T] = TaskResult  # type: ignore
    tools: list[MCP | Tool] | None = None
    reflection: bool = False
    _context: dict[str, Any] = field(init=False, default_factory=dict)

    def __setitem__(self, key: str, value: Any) -> None:
        self._context[key] = value

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

    def process(self) -> str | T:
        print(self.tools)
        print(self.response_format)

        @react(tools=self.tools, response_format=self.response_format)  # type: ignore
        def task(context: str, task: str) -> None:
            return

        result = task(self.context, self.description)

        if self.reflection:
            advice = self._reflect(self.context, self.description, result)
            self["Improvement Advice"] = advice
            self["Result"] = result

            result = task(self.context, self.description)

        return result
