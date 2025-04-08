from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, ParamSpec

from blinker import NamedSignal, signal


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not record.msg:
            self._style._fmt = "%(asctime)s - %(id)s - %(module_name)s"
        else:
            self._style._fmt = "%(asctime)s - %(id)s - %(module_name)s - %(message)s"
        return super().format(record)


# Ensure the logs directory exists
Path("logs").mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("MessageBusLogger")
logger.setLevel(logging.INFO)
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
handler = logging.FileHandler(f"logs/message_bus_{timestamp}.log")
formatter = CustomFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
P = ParamSpec("P")


@dataclass
class MessageBus:
    name: str
    module: str = ""
    signal: ClassVar[NamedSignal] = signal("uglychain")
    _map: ClassVar[dict[str, dict[str, MessageBus]]] = field(default={})

    def send(self, message: object = "", **kwargs: Any) -> None:
        if message:
            kwargs.update(message=message)
        # Log the message, module, and kwargs
        logger.info(message, extra={"module_name": self.module, "id": self.name, "kwargs": kwargs})
        self.signal.send(f"{self.name}_{self.module}", **kwargs)

    def regedit(self, func: Callable[P, None]) -> Callable[P, None]:
        @functools.wraps(func)
        def warper(sender: Any, *args: P.args, **kwargs: P.kwargs) -> None:
            return func(*args, **kwargs)

        self.signal.connect_via(f"{self.name}_{self.module}")(warper)
        return func

    @classmethod
    def get(cls, name: str, module: str = "") -> MessageBus:
        if name not in cls._map:
            cls._map[name] = {}
        if module not in cls._map[name]:
            cls._map[name][module] = cls(name, module)
        return cls._map[name][module]
