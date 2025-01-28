from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

import rich
from rich.columns import Columns
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm
from rich.table import Table, box

from .config import config
from .schema import Messages

MAX_AGRS: int = 5
MAX_ARGS_LEN: int = 8


@dataclass
class Console:
    show_base_info: bool = True
    show_progress: bool = True
    show_api_params: bool = True
    show_result: bool = True
    show_message: bool = True
    show_react: bool = False
    console: rich.console.Console = field(init=False, default_factory=rich.console.Console)
    progress: Progress = field(init=False, default_factory=Progress)
    messages_table: Table = field(init=False, default_factory=Table)
    _live: Live = field(init=False)

    def __post_init__(self) -> None:
        self._init_messages_table()

    def _get_live(self) -> Live:
        if not hasattr(self, "_live") or not self._live:
            self._live = Live(self.group, console=self.console, auto_refresh=False)
        if not self._live.is_started:
            self._live.start(refresh=True)
        return self._live

    def _update_live(self) -> None:
        live = self._get_live()
        live.update(self.group, refresh=True)

    def _stop_live(self) -> None:
        if hasattr(self, "_live") and self._live and self._live.is_started:
            self._live.stop()

    def stop(self) -> None:
        self._stop_live()

    @property
    def group(self) -> Group:
        _group = []
        if self.show_message:
            _group.append(self.messages_table)
        return Group(*_group)

    def init(self) -> None:
        self.show_base_info = self.show_base_info and config.verbose
        self.show_progress = self.show_progress and not config.verbose
        self.progress.disable = not self.show_progress

        self.show_message = self.show_message and config.verbose
        self.show_api_params = self.show_api_params and config.verbose
        self.show_result = self.show_result and config.verbose

    def _init_messages_table(self) -> None:
        self.messages_table = Table(title="Prompt", box=box.SIMPLE, show_header=False, expand=True)
        self.messages_table.add_column("角色", justify="right", no_wrap=True)
        self.messages_table.add_column("内容")

    def log(self, prompt: str, condition: bool = True, **kwargs: Any) -> None:
        if not config.verbose or not condition:
            return
        self.console.print(Panel(prompt, box=box.SIMPLE), **kwargs)

    def rule(self, title: str = "", condition: bool = True, **kwargs: Any) -> None:
        if not config.verbose or not condition:
            return
        self.console.rule(title=title, **kwargs)

    def log_model_usage_pre(
        self,
        model: str,
        func: Callable,
        args: tuple[object, ...],
        kwargs: dict[str, Any],
    ) -> None:
        if not self.show_base_info:
            return
        base_table = Table(box=box.SIMPLE, show_header=False)
        base_table.add_column(style="green")
        base_table.add_column(style="blue")
        base_table.add_row("Model", model)
        base_table.add_row("Func", _format_func_call(func, *args, **kwargs))
        self.console.print(base_table)

    def log_progress_start(self, n: int) -> None:
        self._task_id = self.progress.add_task("模型进度", total=n)
        self.progress.start()

    def log_progress_intermediate(self) -> None:
        self.progress.update(self._task_id, advance=1)

    def log_progress_end(self) -> None:
        self.progress.stop()

    def log_messages(self, messages: Messages) -> None:
        if not self.show_message:
            return
        self._init_messages_table()
        for message in messages:
            if message["role"] == "system":
                style = "bold green"
            elif message["role"] == "user":
                style = "italic yellow"
            else:
                style = "italic blue"
            self.messages_table.add_row(str(message["role"]), str(message["content"]), style=style)
        self._update_live()

    def log_api_params(
        self,
        api_params: dict[str, Any],
    ) -> None:
        if not self.show_api_params:
            return
        if api_params:
            if "tools" in api_params and api_params["tools"]:
                params_table = Table(title="Tools", box=box.SIMPLE, expand=True)
                params_table.add_column("Name", justify="right", no_wrap=True)
                params_table.add_column("Parameters", justify="center")
                for tool in api_params["tools"]:
                    params_table.add_row(
                        tool["function"]["name"], json.dumps(tool["function"]["parameters"], ensure_ascii=False)
                    )
                self.console.print(params_table)

    def log_results(self, result: list) -> None:
        if not self.show_result:
            return
        self.console.print(
            Columns([i.model_dump_json(indent=2) if not isinstance(i, str) else i for i in result]), no_wrap=False
        )

    def call_tool_confirm(self, name: str, args: dict[str, Any]) -> bool:
        if config.need_confirm and name not in ["final_answer", "user_input"]:
            self.console.print(
                Panel(
                    json.dumps(args, indent=2, ensure_ascii=False),
                    title=name,
                )
            )
            return Confirm.ask("Do you confirm to run this tool?", console=self.console, show_default=True)
        elif self.show_react and config.verbose:
            self.console.print(
                Panel(
                    json.dumps(args, indent=2, ensure_ascii=False),
                    title=name,
                )
            )
        return True

    def off(self) -> None:
        self.show_base_info = False
        self.show_progress = False
        self.show_api_params = False
        self.show_result = False
        self.progress.disable = True


class PauseLive:
    def __init__(self, live: Live) -> None:
        self._live = live

    def __enter__(self) -> Live:
        self._live.stop()
        return self._live

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self._live.start()


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


def _format_func_call(func: Callable, *args: Any, **kwargs: Any) -> str:
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
