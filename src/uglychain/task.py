from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic

from pydantic import BaseModel, Field

from .llm import llm
from .react import react
from .schema import T
from .tool import MCP, Tool


class Condition(BaseModel):
    value: bool = Field(description="condition judgment results.")


@dataclass
class Task(Generic[T]):
    description: str
    condition: str = ""
    response_format: type[T] | None = None
    tools: list[MCP | Tool] | None = None
    reflection: bool = False
    _context: dict[str, Any] = field(init=False, default_factory=dict)

    @property
    def context(self) -> str:
        str = ""
        for key in self._context.keys():
            str += f"<{key}>\n{self._context[key]!r}\n</{key}>\n"
        return str

    @staticmethod
    @llm("openai:gpt-4o", response_format=Condition, need_retry=True)
    def _judge(context: str, condition: str) -> None:
        """Determine whether the conditions are met. Return a boolean value."""
        pass

    @staticmethod
    @llm(need_retry=True)
    def _reflect(context: str, task: str, result: Any) -> None:
        """Reflect on the result of the task. Give advice on how to improve the task."""
        pass

    def _run(self) -> str | T:
        if self.condition and not self._judge(self.context, self.condition).value:
            return str(self.context)

        @react(tools=self.tools, response_format=self.response_format)  # type: ignore
        def task(context: str, task: str) -> None:
            return

        result = task(self.context, self.description)

        if self.reflection:
            advice = self._reflect(self.context, self.description, result)
            self._context["Improvement Advice"] = advice
            self._context["Result"] = result

            result = task(self.context, self.description)

        return result
