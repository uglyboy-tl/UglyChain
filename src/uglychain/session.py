from __future__ import annotations

import inspect
import logging
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from .config import config
from .console import BaseConsole, SimpleConsole
from .utils import MessageBus

MAX_AGRS: int = 5
MAX_ARGS_LEN: int = 8


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not record.msg:
            self._style._fmt = "%(asctime)s - %(id)s - %(module_name)s"
        else:
            self._style._fmt = "%(asctime)s - %(id)s - %(module_name)s - %(message)s"
        return super().format(record)


# Ensure the logs directory exists
if config.session_log:
    Path("logs").mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("SessionLogger")
logger.setLevel(logging.INFO)
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
handler = logging.FileHandler(f"logs/session_{timestamp}.log")
formatter = CustomFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class Session:
    session_type: Literal["llm", "react"] = "llm"
    uuid: uuid.UUID = field(init=False, default_factory=uuid.uuid1)
    info: dict[str, str] = field(init=False, default_factory=dict)
    consoles: list[BaseConsole] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.console_register(SimpleConsole())

    def console_register(self, console: BaseConsole) -> None:
        self.consoles.append(console)
        MessageBus.get(self.id, "base_info").regedit(console.base_info)
        MessageBus.get(self.id, "messages").regedit(console.messages)
        if self.session_type == "llm":
            MessageBus.get(self.id, "api_params").regedit(console.api_params)
            MessageBus.get(self.id, "results").regedit(console.results)
            MessageBus.get(self.id, "progress_start").regedit(console.progress_start)
            MessageBus.get(self.id, "progress_intermediate").regedit(console.progress_intermediate)
            MessageBus.get(self.id, "progress_end").regedit(console.progress_end)
        elif self.session_type == "react":
            MessageBus.get(self.id, "rule").regedit(console.rule)
            MessageBus.get(self.id, "action").regedit(console.action_info)
            MessageBus.get(self.id, "tool").regedit(console.tool_info)

    @property
    def model(self) -> str:
        return self.info.get("model", "")

    @model.setter
    def model(self, model: str) -> None:
        self.info["model"] = model

    @property
    def func(self) -> str:
        return self.info.get("func", "")

    @func.setter
    def func(self, func: str) -> None:
        if "func" not in self.info:
            self.info["func"] = func

    @property
    def id(self) -> str:
        id = self.info.get("id")
        if id:
            return id
        else:
            return self.uuid.hex

    def send(self, module: str, message: Any = None, /, **kwargs: Any) -> None:
        # Log the message, module, and kwargs
        if config.session_log:
            if isinstance(message, Iterator):
                message = "".join(message)
            logger.info(message, extra={"id": self.id, "module_name": module, "kwargs": kwargs})
        MessageBus.get(self.id, module).send(message, **kwargs)

    def show_base_info(self) -> None:
        self.send("base_info", self.func, model=self.model, id=self.id)
        for console in self.consoles:
            console.show_base_info = False

    def call_tool_confirm(self, name: str) -> bool:
        return self.consoles[0].call_tool_confirm(name)

    @staticmethod
    def format_func_call(func: Callable, *args: Any, **kwargs: Any) -> str:
        # 获取函数的参数信息
        signature = inspect.signature(func)
        bound_arguments = signature.bind(*args, **kwargs)
        bound_arguments.apply_defaults()

        # 构建参数字符串
        args_str = []
        for name, value in bound_arguments.arguments.items():
            if isinstance(value, list | dict | set | tuple):
                end_str = ""
                display_value = ""
                if len(value) > 2:
                    end_str = ",..."
                if isinstance(value, dict):
                    display_value = f"{{{', '.join([f'{_format_arg_str(k)}: {_format_arg_str(value[k])}' for k in list(value)[:2]])}{end_str}}}"
                elif isinstance(value, tuple):
                    display_value = f"({', '.join([_format_arg_str(i) for i in value[:2]])}{end_str})"
                elif isinstance(value, set):
                    display_value = f"{{{', '.join([_format_arg_str(i) for i in list(value)[:2]])}{end_str}}}"
                elif isinstance(value, list):
                    display_value = f"[{', '.join([_format_arg_str(i) for i in value[:2]])}{end_str}]"
                args_str.append(f"{name}={display_value}")
            else:
                args_str.append(f"{name}={_format_arg_str(value)}")

        # 构建最终的函数调用字符串
        if len(args_str) <= MAX_AGRS:
            func_call_str = f"{func.__name__}({', '.join(args_str)})"
        else:
            func_call_str = f"{func.__name__}({', '.join(args_str[:MAX_AGRS])}, ...)"
        return func_call_str


def _format_arg_str(arg_str: Any, max_len: int = MAX_ARGS_LEN) -> str:
    if isinstance(arg_str, str):
        if len(arg_str) > max_len:
            return f"'{arg_str[:max_len].strip()}...'"
        else:
            return f"'{arg_str}'"
    else:
        arg_str = repr(arg_str)
        if len(arg_str) > max_len:
            return f"{arg_str[:max_len].strip()}..."
        else:
            return arg_str
