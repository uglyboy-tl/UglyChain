from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from uglychain.config import config
from uglychain.schema import Messages

from .base import BaseConsole

# 创建一个新的 logger 实例
logger = logging.getLogger("SimpleConsoleLogger")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@dataclass
class SimpleConsole(BaseConsole):
    def base_info(self, message: str = "", model: str = "", id: str = "") -> None:
        if not config.verbose or not self.show_base_info:
            return
        logger.info(f"\nID:    {id}")
        logger.info(f"Model: {model}")
        logger.info(f"Func:  {message}")

    def rule(self, message: str = "", **kwargs: Any) -> None:
        if not config.verbose or not self.show_react:
            return
        logger.info(f"\n--- {message} ---")

    def action_message(self, message: str = "", **kwargs: Any) -> None:
        if not config.verbose or not self.show_react:
            return
        logger.info(message)

    def tool_message(self, message: str = "", arguments: dict[str, Any] | None = None) -> None:
        if (
            config.need_confirm
            and message in ["final_answer", "user_input"]
            and (not config.verbose or not self.show_react)
        ):
            return
        logger.info(f"==== {message} ====")
        logger.info(json.dumps(arguments, indent=2, ensure_ascii=False))
        logger.info("=======================")

    def api_params(self, message: dict[str, Any]) -> None:
        return

    def results(self, message: list | Iterator) -> None:
        if not config.verbose or not self.show_result:
            return
        if isinstance(message, Iterator):
            for chunk in message:
                if chunk is not None:
                    print(chunk, end="", flush=True)
        else:
            for i in message:
                logger.info(i)

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
