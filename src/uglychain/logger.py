from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Logger:
    def model_usage_logger_pre(
        self,
        model: str,
        prompt: Callable,
        args: tuple[str | list[str], ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Add prompt to the logger."""
        print(f"开始处理 {prompt.__name__}")
        print(f"模型: {model}")
        print(f"参数列表: {','.join([repr(arg) for arg in args] + [k+':'+repr(v) for k,v in kwargs.items()])}")

    def model_usage_logger_post_start(self, n: int) -> None:
        """Add response to the logger."""
        print(f"将返回 {n} 条结果")

    def model_usage_logger_post_info(
        self,
        messages: list[dict[str, str]],
        merged_api_params: dict[str, Any],
    ) -> None:
        """Add response to the logger."""
        print(f"消息列表: {messages}")
        print(f"参数: {merged_api_params}")

    def model_usage_logger_post_intermediate(self, result: Any) -> None:
        """Add response to the logger."""
        if isinstance(result, list):
            print(f"返回结果: {[repr(i) for i in result]}")
        else:
            print(f"返回结果: {repr(result)}")

    def model_usage_logger_post_end(self) -> None:
        """Add response to the logger."""
        pass
