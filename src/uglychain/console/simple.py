from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from uglychain.config import config
from uglychain.schema import Messages

from .base import BaseConsole


@dataclass
class SimpleConsole(BaseConsole):
    def base_info(self, message: str = "", model: str = "", id: str = "") -> None:
        if not config.verbose or not self.show_base_info:
            return
        print(f"\nID:    {id}")
        print(f"Model: {model}")
        print(f"Func:  {message}")

    def rule(self, message: str = "", **kwargs: Any) -> None:
        if not config.verbose or not self.show_react:
            return
        print(f"\n--- {message} ---")

    def action_message(self, message: str = "", **kwargs: Any) -> None:
        if not config.verbose or not self.show_react:
            return
        print(message)

    def tool_message(self, message: str = "", arguments: dict[str, Any] | None = None) -> None:
        if (
            config.need_confirm
            and message in ["final_answer", "user_input"]
            and (not config.verbose or not self.show_react)
        ):
            return
        print(f"==== {message} ====")
        print(json.dumps(arguments, indent=2, ensure_ascii=False))
        print("=======================")

    def api_params(self, api_params: dict[str, Any]) -> None:
        return

    def results(self, result: list | Iterator) -> None:
        if not config.verbose or not self.show_result:
            return
        if isinstance(result, Iterator):
            for chunk in result:
                if chunk is not None:
                    print(chunk, end="", flush=True)
        else:
            for i in result:
                print(i)

    def progress_start(self, n: int) -> None:
        return

    def progress_intermediate(self) -> None:
        return

    def progress_end(self) -> None:
        return

    def log_messages(self, messages: Messages) -> None:
        return

    def call_tool_confirm(self, name: str) -> bool:
        return True
