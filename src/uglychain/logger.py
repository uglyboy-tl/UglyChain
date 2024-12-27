from __future__ import annotations

from collections.abc import Callable
from typing import Any

from rich.columns import Columns
from rich.console import Console
from rich.table import Table, box

from .config import config


class Logger:
    def __init__(self) -> None:
        self.if_log = config.verbose
        self.console = Console()

    def model_usage_logger_pre(
        self,
        model: str,
        prompt: Callable,
        args: tuple[str | list[str], ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Add prompt to the logger."""
        if not self.if_log:
            return
        table = Table(title=prompt.__name__, box=box.SIMPLE)
        table.add_column("名称", justify="center", no_wrap=True)
        table.add_column("信息", justify="center")
        table.add_row("模型", model)
        table.add_row(
            "参数信息", ",".join([repr(arg) for arg in args] + [k + ":" + repr(v) for k, v in kwargs.items()])
        )
        self.console.print(table)

    def model_usage_logger_post_start(self, n: int) -> None:
        """Add response to the logger."""
        if not self.if_log:
            return
        # print(f"将返回 {n} 条结果")

    def model_usage_logger_post_info(
        self,
        messages: list[dict[str, str]],
        merged_api_params: dict[str, Any],
    ) -> None:
        """Add response to the logger."""
        if not self.if_log:
            return
        table = Table(title="Prompt", box=box.SIMPLE, show_header=False)
        table.add_column("角色", justify="right", no_wrap=True)
        table.add_column("内容", justify="left")
        for message in messages:
            if message["role"] == "system":
                style = "bold green"
            elif message["role"] == "user":
                style = "italic blue"
            else:
                style = ""
            table.add_row(message["role"], message["content"], style=style)
        self.console.print(table)

    def model_usage_logger_post_intermediate(self, result: list) -> None:
        """Add response to the logger."""
        if not self.if_log:
            return
        self.console.print(Columns([i.model_dump_json(indent=2) if not isinstance(i, str) else i for i in result]))

    def model_usage_logger_post_end(self) -> None:
        """Add response to the logger."""
        if not self.if_log:
            return
