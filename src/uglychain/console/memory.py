from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from uglychain.schema import Messages

from .base import EmptyConsole


@dataclass
class Memory(EmptyConsole):
    memory: ClassVar[dict[str, list[Messages]]] = {}

    def messages(self, message: Messages, **kwargs: Any) -> None:
        history = self.memory.get(self.id, [])
        history.append(message)
        self.memory[self.id] = history
