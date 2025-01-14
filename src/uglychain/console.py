from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import rich
from rich.columns import Columns
from rich.progress import Progress
from rich.table import Table, box

from .config import config


class Console:
    def __init__(self) -> None:
        self.if_log = config.verbose
        self.console = rich.console.Console()
        self.progress = Progress(disable=self.if_log or not config.show_progress)

    def log_model_usage_pre(
        self,
        model: str,
        prompt: Callable,
        args: tuple[object, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Add prompt to the logger."""
        if not self.if_log:
            return

    def log_progress_start(self, n: int) -> None:
        self._task_id = self.progress.add_task("模型进度", total=n)
        self.progress.start()

    def log_progress_intermediate(self) -> None:
        self.progress.update(self._task_id, advance=1)

    def log_progress_end(self) -> None:
        self.progress.stop()

    def log_model_usage_post_info(
        self,
        messages: list[dict[str, str]],
        merged_api_params: dict[str, Any],
    ) -> None:
        if not self.if_log:
            return
        table = Table(title="Prompt", box=box.SIMPLE, show_header=False)
        table.add_column("角色", justify="right", no_wrap=True)
        table.add_column("内容", justify="left")
        for message in messages:
            if message["role"] == "system":
                style = "bold green"
            elif message["role"] == "user":
                style = "italic yellow"
            else:
                style = "italic blue"
            table.add_row(message["role"], message["content"], style=style)
        self.console.print(table)
        if merged_api_params:
            if "tools" in merged_api_params:
                params_table = Table(title="Tools", box=box.SIMPLE)
                params_table.add_column("Name", justify="right", no_wrap=True)
                params_table.add_column("Parameters", justify="center")
                for tool in merged_api_params["tools"]:
                    params_table.add_row(
                        tool["function"]["name"], json.dumps(tool["function"]["parameters"], ensure_ascii=False)
                    )
                self.console.print(params_table)

    def log_model_usage_post_intermediate(self, result: list) -> None:
        self.log_progress_intermediate()
        if not self.if_log:
            return
        self.console.print(Columns([i.model_dump_json(indent=2) if not isinstance(i, str) else i for i in result]))
