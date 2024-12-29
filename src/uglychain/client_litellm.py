from __future__ import annotations

import threading
from typing import Any

from litellm import CustomStreamWrapper, completion


class Client:
    # 单例模式缓存 Client 实例
    _client_instance: Client | None = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> Client:
        """Get the singleton instance of the Client class."""
        with cls._lock:
            if cls._client_instance is None:
                cls._client_instance = cls()
        return cls._client_instance

    @classmethod
    def reset(cls) -> None:
        """
        将客户端实例重置为 None。

        该函数用于清除全局客户端实例变量，
        确保客户端状态在后续配置或使用前被重置。
        """
        cls._client_instance = None

    @classmethod
    def generate(
        cls,
        model: str,
        messages: list[dict[str, str]],
        **api_params: Any,
    ) -> list[Any]:
        try:
            response = completion(
                model=model.replace(":", "/"),
                messages=messages,
                **api_params,
            )
        except Exception as e:
            raise RuntimeError(f"生成响应失败: {e}") from e
        if isinstance(response, CustomStreamWrapper) or not response.choices:
            raise ValueError("No choices returned from the model")
        return response.choices
