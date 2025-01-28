from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic

from pydantic import BaseModel, Field

from uglychain import llm, react
from uglychain.schema import T
from uglychain.tool import MCP, Tool


class TaskResult(BaseModel):
    response: str = Field(description="The final response of the task.")
    steps: list[str] = Field(description="Key steps to solve the task.")


@dataclass
class BasicTask:
    _context: dict[str, Any] = field(init=False, default_factory=dict)

    def __setitem__(self, key: str, value: Any) -> None:
        self._context[key] = value

    @property
    def context(self) -> str:
        str = ""
        for key in self._context.keys():
            str += f"<{key}>\n{self._context[key]!r}\n</{key}>\n"
        return str


@dataclass
class Task(BasicTask, Generic[T]):
    description: str
    response_format: type[T] = TaskResult  # type: ignore
    tools: list[MCP | Tool] | None = None
    reflection: bool = False
    _context: dict[str, Any] = field(init=False, default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.description, self.response_format, self.tools, self.reflection))

    @staticmethod
    @llm(need_retry=True)
    def _reflect(context: str, task: str, result: Any) -> None:
        """Reflect on the result of the task. Give advice on how to improve the task."""
        pass

    def process(self) -> str | T:
        # print(self.tools)
        # print(self.response_format)

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


class Condition(BaseModel):
    value: bool = Field(description="condition judgment results.")


@dataclass
class LogicTask(BasicTask):
    condition: str = ""
    repeat: bool = False

    @staticmethod
    @llm("openai:gpt-4o", response_format=Condition, need_retry=True)
    def _judge(context: str, condition: str) -> None:
        """Determine whether the conditions are met. Return a boolean value."""
        pass

    def _run(self) -> Any:
        pass

    def process(self) -> Any:
        if not self.condition:
            return self.context
        repeat = True
        while self._judge(self.context, self.condition).value and repeat:
            repeat = self.repeat
            result = self._run()
            self._context.update({"result": result})
