from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

from blinker import NamedSignal, signal

from .schema import P


@dataclass
class Logger:
    name: str
    module: str = ""
    signal: ClassVar[NamedSignal] = signal("uglychain")
    _map: ClassVar[dict[str, dict[str, Logger]]] = field(default={})

    def info(self, message: str = "", **kwargs: Any) -> None:
        if message:
            kwargs.update(message=message)
        self.signal.send(f"{self.name}_{self.module}", **kwargs)

    def regedit(self, func: Callable[P, None]) -> Callable[P, None]:
        @functools.wraps(func)
        def warper(sender: Any, *args: P.args, **kwargs: P.kwargs) -> None:
            return func(*args, **kwargs)

        self.signal.connect_via(f"{self.name}_{self.module}")(warper)
        return func

    @classmethod
    def get(cls, name: str, module: str = "") -> Logger:
        if name not in cls._map:
            cls._map[name] = {}
        if module not in cls._map[name]:
            cls._map[name][module] = cls(name, module)
        return cls._map[name][module]
