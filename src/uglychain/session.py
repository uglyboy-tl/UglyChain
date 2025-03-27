from __future__ import annotations

import inspect
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .console import Console
from .logger import Logger
from .react_action import Action
from .tool import Tool

MAX_AGRS: int = 5
MAX_ARGS_LEN: int = 8


@dataclass
class Session:
    type: str = "llm"
    uuid: uuid.UUID = field(init=False, default_factory=uuid.uuid1)
    info: dict[str, str] = field(init=False, default_factory=dict)
    console: Console = field(default_factory=Console)

    def __post_init__(self) -> None:
        Logger.get(self.id, "base_info").regedit(self.console.base_info)
        if self.type == "llm":
            Logger.get(self.id, "api_params").regedit(self.console.api_params)
            Logger.get(self.id, "results").regedit(self.console.results)
            Logger.get(self.id, "progress_start").regedit(self.console.progress_start)
            Logger.get(self.id, "progress_intermediate").regedit(self.console.progress_intermediate)
            Logger.get(self.id, "progress_end").regedit(self.console.progress_end)
            Logger.get(self.id, "messages").regedit(self.console.log_messages)
        elif self.type == "react":
            self.console.show_react = True
            Logger.get(self.id, "rule").regedit(self.console.rule)
            Logger.get(self.id, "action").regedit(self.console.action_message)
            Logger.get(self.id, "tool").regedit(self.console.tool_message)

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
        return self.uuid.hex

    def log(self, module: str, message: str = "", /, **kwargs: Any) -> None:
        Logger.get(self.id, module).info(message, **kwargs)

    def show_base_info(self) -> None:
        self.log("base_info", self.func, model=self.model)
        self.console.show_base_info = False

    def process(self, act: Action) -> None:
        self.log("tool", act.tool, arguments=act.args)
        if not self.call_tool_confirm(act.tool):
            act.obs = "User cancelled. Please find other ways to solve this problem."
            return
        try:
            result = Tool.call_tool(act.tool, **act.args)
            act.obs, act.image = result if isinstance(result, tuple) else (result, None)
            self.log("action", _short_result(act.obs), style="bold green")
        except Exception as e:
            act.obs = f"Error: {e}"
            self.log("action", act.obs, style="bold red")

    def call_tool_confirm(self, name: str) -> bool:
        return self.console.call_tool_confirm(name)

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


def _short_result(result: str) -> str:
    lines = result.split("\n")
    if len(lines) > 10:
        return "\n".join(lines[:10]) + "\n..."
    elif len(result) > 200:
        return result[:200] + "..."
    else:
        return result
