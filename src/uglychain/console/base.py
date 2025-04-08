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
    def base_info(self, message: str = "", model: str = "", id: str = "") -> None:
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
    def api_params(self, message: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def results(self, message: list | Iterator) -> None:
        pass

    @abstractmethod
    def progress_start(self, message: int) -> None:
        pass

    @abstractmethod
    def progress_intermediate(self) -> None:
        pass

    @abstractmethod
    def progress_end(self) -> None:
        pass

    @abstractmethod
    def log_messages(self, message: Messages) -> None:
        pass

    @abstractmethod
    def call_tool_confirm(self, message: str) -> bool:
        pass


class EmptyConsole(BaseConsole):
    def base_info(self, message: str = "", model: str = "", id: str = "") -> None:
        return

    def rule(self, message: str = "", **kwargs: Any) -> None:
        return

    def action_message(self, message: str = "", **kwargs: Any) -> None:
        return

    def tool_message(self, message: str = "", arguments: dict[str, Any] | None = None) -> None:
        return

    def api_params(self, message: dict[str, Any]) -> None:
        return

    def results(self, message: list | Iterator) -> None:
        return

    def progress_start(self, message: int) -> None:
        return

    def progress_intermediate(self) -> None:
        return

    def progress_end(self) -> None:
        return

    def log_messages(self, message: Messages) -> None:
        return

    def call_tool_confirm(self, message: str) -> bool:
        return True
