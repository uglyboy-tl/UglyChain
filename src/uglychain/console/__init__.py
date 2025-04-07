from __future__ import annotations

from .base import BaseConsole
from .rich import RichConsole


def get_console() -> RichConsole:
    return RichConsole()


__all__ = [
    "get_console",
    "BaseConsole",
]
