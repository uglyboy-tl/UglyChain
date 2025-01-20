from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import rich
from rich.columns import Columns
from rich.console import Group
from rich.live import Live
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.table import Table, box

from .config import config

REACT_NAME = {
    "thought": "Thought",
    "tool": "Action",
    "args": "Action Input",
    "obs": "Observation",
}

REACT_STYLE = {
    "thought": "italic yellow",
    "tool": "bold red",
    "args": "bold red",
    "obs": "bold green",
}


@dataclass
class Console:
    show_base_info: bool = True
    show_progress: bool = True
    show_message: bool = True
    show_api_params: bool = True
    show_result: bool = True
    show_react: bool = True
    console: rich.console.Console = field(init=False, default_factory=rich.console.Console)
    progress: Progress = field(init=False, default_factory=Progress)
    react_table: Table = field(init=False, default_factory=Table)
    group: Group = field(init=False)
    _live: Live = field(init=False)

    def __post_init__(self) -> None:
        self._init_react_table()
        self.group = Group(self.react_table)

    def init(self):
        self.show_base_info = self.show_base_info and config.verbose
        self.show_progress = self.show_progress and not config.verbose
        self.progress.disable = not self.show_progress

        self.show_message = self.show_message and config.verbose
        self.show_api_params = self.show_api_params and config.verbose
        self.show_result = self.show_result and config.verbose

    def _init_react_table(self):
        self.react_table.box = box.SIMPLE
        self.react_table.show_header = False
        self.react_table.expand = True
        self.react_table.add_column("Type")
        self.react_table.add_column("Information")

    def log_model_usage_pre(
        self,
        model: str,
        func: Callable,
        args: tuple[object, ...],
        kwargs: dict[str, Any],
    ) -> None:
        if not self.show_base_info:
            return
        self.console.print(f"[bold green]Model[/bold green]: {model}")

    def log_progress_start(self, n: int) -> None:
        self._task_id = self.progress.add_task("模型进度", total=n)
        self.progress.start()

    def log_progress_intermediate(self) -> None:
        self.progress.update(self._task_id, advance=1)

    def log_progress_end(self) -> None:
        self.progress.stop()

    def log_messages(self, messages: list[dict[str, str]]) -> None:
        if not self.show_message:
            return
        messages_table = Table(title="Prompt", box=box.SIMPLE, show_header=False, expand=True)
        messages_table.add_column("角色", justify="right", no_wrap=True)
        messages_table.add_column("内容")
        for message in messages:
            if message["role"] == "system":
                style = "bold green"
            elif message["role"] == "user":
                style = "italic yellow"
            else:
                style = "italic blue"
            messages_table.add_row(message["role"], message["content"], style=style)
        self.console.print(messages_table)

    def log_api_params(
        self,
        api_params: dict[str, Any],
    ) -> None:
        if not self.show_api_params:
            return
        if api_params:
            if "tools" in api_params:
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
        self.console.print(Columns([i.model_dump_json(indent=2) if not isinstance(i, str) else i for i in result]))

    def log_react(self, act: dict[str, Any]) -> None:
        if not self.show_react:
            return
        for key in ["thought", "tool", "args", "obs"]:
            self.react_table.add_row(REACT_NAME[key], str(act[key]).strip(), style=REACT_STYLE[key])
        self._update_live()

    def input(self, prompt: str, default: str = "") -> str:
        return Prompt.ask(prompt, console=self.console, default=default)

    def confirm(self, prompt: str, default: bool = True) -> bool:
        return Confirm.ask(prompt, console=self.console, show_default=default)

    def off(self) -> None:
        self.show_base_info = False
        self.show_progress = False
        self.show_message = False
        self.show_api_params = False
        self.show_result = False
        self.progress.disable = True

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

    def stop(self):
        self._stop_live()
