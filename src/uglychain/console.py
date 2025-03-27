from __future__ import annotations

import json
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

    def _init_messages_table(self) -> None:
        self.messages_table = Table(title="Prompt", box=box.SIMPLE, show_header=False, expand=True)
        self.messages_table.add_column("角色", justify="right", no_wrap=True)
        self.messages_table.add_column("内容")

    def base_info(self, message: str = "", model: str = "") -> None:
        if not config.verbose or not self.show_base_info:
            return
        base_table = Table(box=box.SIMPLE, show_header=False)
        base_table.add_column(style="green")
        base_table.add_column(style="blue")
        base_table.add_row("Model", model)
        base_table.add_row("Func", message)
        self.console.print(base_table)

    def rule(self, message: str = "", **kwargs: Any) -> None:
        if not config.verbose or not self.show_react:
            return
        self.console.rule(title=message, **kwargs)

    def action_message(self, message: str = "", **kwargs: Any) -> None:
        if not config.verbose or not self.show_react:
            return
        self.console.print(Panel(message, box=box.SIMPLE), **kwargs)

    def tool_message(self, message: str = "", arguments: dict[str, Any] | None = None) -> None:
        if (
            config.need_confirm
            and message in ["final_answer", "user_input"]
            and (not config.verbose or not self.show_react)
        ):
            return
        self.console.print(
            Panel(
                json.dumps(arguments, indent=2, ensure_ascii=False),
                title=message,
            )
        )

    def api_params(self, api_params: dict[str, Any]) -> None:
        if not config.verbose or not self.show_api_params:
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

    def results(self, result: list) -> None:
        if not config.verbose or not self.show_result:
            return
        self.console.print(
            Columns([i.model_dump_json(indent=2) if not isinstance(i, str) else i for i in result]), no_wrap=False
        )

    def progress_start(self, n: int) -> None:
        self.progress.disable = not self.show_progress or config.verbose
        if n > 1:
            self.show_result = False
        else:
            self.progress.disable = True
        self._task_id = self.progress.add_task("模型进度", total=n)
        self.progress.start()

    def progress_intermediate(self) -> None:
        self.progress.update(self._task_id, advance=1)

    def progress_end(self) -> None:
        self.progress.stop()

    def log_messages(self, messages: Messages) -> None:
        if not config.verbose or not self.show_message:
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

    def call_tool_confirm(self, name: str) -> bool:
        if config.need_confirm and name not in ["final_answer", "user_input"]:
            return Confirm.ask("Do you confirm to run this tool?", console=self.console, show_default=True)
        return True


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
