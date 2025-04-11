from __future__ import annotations

import json
import logging
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from uglychain.config import config
from uglychain.utils import Stream

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

    def _process_iterator(self, iterator: Iterator) -> None:
        """在单独的线程中处理迭代器，避免阻塞主线程"""
        for chunk in iterator:
            if chunk is not None:
                print(chunk, end="", flush=True)

    def results(self, message: list | Stream | None = None) -> None:
        if message is None:
            message = list()
        if not config.verbose or not self.show_result:
            return

        if isinstance(message, Stream):
            # 创建并启动一个新线程来处理迭代器
            thread = threading.Thread(target=self._process_iterator, args=(message.iterator,))
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程会自动结束
            thread.start()
        else:
            for i in message:
                logger.info(i)
