from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from uglychain.config import config

from .base import EmptyConsole

# 创建一个新的 logger 实例
logger = logging.getLogger("SimpleConsoleLogger")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@dataclass
class SimpleConsole(EmptyConsole):
    def base_info(self, message: str = "", model: str = "") -> None:
        if not config.verbose or not self.show_base_info:
            return
        logger.info(f"\nID:    {self.id}")
        logger.info(f"Model: {model}")
        logger.info(f"Func:  {message}")

    def rule(self, message: str = "", **kwargs: Any) -> None:
        if not config.verbose or not self.show_react:
            return
        logger.info(f"\n--- {message} ---")

    def action_info(self, message: str = "", **kwargs: Any) -> None:
        if not config.verbose or not self.show_react:
            return
        logger.info(message)

    def tool_info(self, message: str = "", arguments: dict[str, Any] | None = None) -> None:
        if (
            config.need_confirm
            and message in ["final_answer", "user_input"]
            and (not config.verbose or not self.show_react)
        ):
            return
        logger.info(f"==== {message} ====")
        logger.info(json.dumps(arguments, indent=2, ensure_ascii=False))
        logger.info("=======================")

    def api_params(self, message: dict[str, Any] | None = None) -> None:
        if message is None:
            message = dict()
        return

    def results(self, message: list | Iterator | None = None) -> None:
        if message is None:
            message = list()
        if not config.verbose or not self.show_result:
            return
        if isinstance(message, Iterator):
            for chunk in message:
                if chunk is not None:
                    print(chunk, end="", flush=True)
        else:
            for i in message:
                logger.info(i)
