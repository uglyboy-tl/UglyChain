from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from uglychain.schema import Messages


@dataclass
class BaseConsole(ABC):
    show_base_info: bool = True
    show_progress: bool = True
    show_api_params: bool = True
    show_result: bool = True
    show_message: bool = True
    show_react: bool = False

    @abstractmethod
    def base_info(self, message: str = "", model: str = "") -> None:
        pass

    @abstractmethod
    def rule(self, message: str = "", **kwargs: Any) -> None:
        pass

    @abstractmethod
    def action_message(self, message: str = "", **kwargs: Any) -> None:
        pass

    @abstractmethod
    def tool_message(self, message: str = "", arguments: dict[str, Any] | None = None) -> None:
        pass

    @abstractmethod
    def api_params(self, api_params: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def results(self, result: list | Iterator) -> None:
        pass

    @abstractmethod
    def progress_start(self, n: int) -> None:
        pass

    @abstractmethod
    def progress_intermediate(self) -> None:
        pass

    @abstractmethod
    def progress_end(self) -> None:
        pass

    @abstractmethod
    def log_messages(self, messages: Messages) -> None:
        pass

    @abstractmethod
    def call_tool_confirm(self, name: str) -> bool:
        pass
