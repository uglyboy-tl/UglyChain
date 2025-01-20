from __future__ import annotations

import threading
from typing import Any

import aisuite

from .schema import Messages


class Client:
    # 单例模式缓存 Client 实例
    _client_instance: aisuite.Client | None = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> aisuite.Client:
        """
        返回一个aisuite的Client实例。

        该函数使用了线程安全的单例模式设计原则，确保在整个应用程序中只有一个Client实例被创建和使用。
        这样做可以节省资源，并确保与Client的所有交互都是通过同一个实例进行的。

        Returns:
            aisuite.Client: aisuite的Client实例。
        """
        if cls._client_instance is None:
            with cls._lock:
                if cls._client_instance is None:
                    cls._client_instance = aisuite.Client()
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
        messages: Messages,
        **api_params: Any,
    ) -> list[Any]:
        try:
            response = cls.get().chat.completions.create(
                model=model,
                messages=messages,
                **api_params,
            )
        except Exception as e:
            raise RuntimeError(f"生成响应失败: {e}") from e
        if not hasattr(response, "choices") or not response.choices:
            raise ValueError("No choices returned from the model")
        return response.choices
