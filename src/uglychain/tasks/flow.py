from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from uglychain import llm

from .task import Task


class Condition(BaseModel):
    value: bool = Field(description="condition judgment results.")


@dataclass
class Flow:
    tasks: list[Task | LogicTask]

    def _run(self) -> Any:
        return


@dataclass
class LogicTask:
    flow: Flow
    condition: str = ""
    repeat: bool = False
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

    def _run(self) -> Any:
        if not self.condition:
            return self.context
        repeat = True
        while self._judge(self.context, self.condition).value and repeat:
            repeat = self.repeat
            result = self.flow._run()
            self._context.update({"result": result})
