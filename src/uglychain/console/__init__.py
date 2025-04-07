from __future__ import annotations

from .base import BaseConsole
from .rich import RichConsole
from .simple import SimpleConsole


def get_console() -> BaseConsole:
    return SimpleConsole()


__all__ = [
    "get_console",
    "BaseConsole",
]
