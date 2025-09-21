"""
该模块定义了与aisuite客户端交互的逻辑，包括客户端的单例管理、消息生成和模型路由。
"""

from __future__ import annotations

import os  # 导入os模块，用于访问环境变量
import threading  # 导入threading模块，用于实现线程安全
from collections.abc import Iterator  # 导入Iterator类型，用于类型提示
from typing import Any  # 导入Any类型，用于类型提示

import aisuite  # 导入aisuite库

from .schema import Messages  # 从当前包导入Messages类型


class Client:
    """
    Client类负责管理aisuite客户端实例，并提供与LLM交互的方法。
    它实现了单例模式，确保在整个应用程序中只有一个aisuite客户端实例。
    """

    # 单例模式缓存 Client 实例
    _client_instance: aisuite.Client | None = None
    # 用于线程安全的锁
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
            with cls._lock:  # 获取锁，确保线程安全
                if cls._client_instance is None:  # 双重检查锁定
                    cls._client_instance = aisuite.Client()  # 创建aisuite客户端实例
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
        model: str,  # 模型名称，例如 "openai:gpt-4o"
        messages: Messages,  # 消息列表，用于LLM的输入
        **api_params: Any,  # 其他API参数
    ) -> Iterator[Any] | list[Any]:
        """
        使用指定的模型和消息生成LLM响应。

        Args:
            model (str): 要使用的模型名称。
            messages (Messages): 发送给模型的对话消息。
            **api_params (Any): 传递给aisuite客户端的额外API参数，例如 `stream=True`。

        Returns:
            Iterator[Any] | list[Any]: 如果是流式响应，则返回一个迭代器；否则返回一个包含响应选择的列表。

        Raises:
            RuntimeError: 如果生成响应失败。
            ValueError: 如果模型没有返回任何选择。
        """
        # 通过路由器获取实际的客户端模型名称
        client_model = _router(model, cls.get())
        try:
            # 调用aisuite客户端的chat completions API
            response = cls.get().chat.completions.create(
                model=client_model,
                messages=messages,
                **api_params,
            )
        except Exception as e:
            # 捕获并重新抛出生成响应时的错误
            raise RuntimeError(f"生成响应失败: {e}") from e

        # 处理流式响应
        if api_params.get("stream", False) and isinstance(response, Iterator):
            # 从流式响应中提取choices
            return (item.choices[0] for item in response if isinstance(item.choices, list) and len(item.choices) > 0)
        # 处理非流式响应，检查是否有choices
        elif not hasattr(response, "choices") or not response.choices:
            raise ValueError("No choices returned from the model")
        else:
            # 断言choices是列表并返回
            assert isinstance(response.choices, list)
            return response.choices


def _router(model: str, client: aisuite.Client) -> str:
    """
    根据模型名称路由到不同的提供商配置。

    Args:
        model (str): 完整的模型名称，例如 "openrouter:gpt-4o"。
        client (aisuite.Client): aisuite客户端实例。

    Returns:
        str: 路由后的模型名称，可能包含提供商前缀。
    """
    # 分割提供商键和模型名称
    provider_key, model_name = model.split(":", 1)
    if provider_key == "openrouter":
        # 如果是openrouter，配置aisuite客户端
        config = {
            "openai": {"api_key": os.getenv("OPENROUTER_API_KEY") or "", "base_url": "https://openrouter.ai/api/v1"}
        }
        client.configure(config)  # 应用配置
        return f"openai:{model_name}"  # 返回带有openai前缀的模型名称
    else:
        return model  # 返回原始模型名称


# 支持多模态模型的集合
SUPPORT_MULTIMODAL_MODELS = {
    "openai:gpt-4o",
    "openai:gpt-4o-mini",
}
