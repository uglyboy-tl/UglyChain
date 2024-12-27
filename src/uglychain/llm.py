from __future__ import annotations

import threading
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

import aisuite

from .config import config
from .response_format import ResponseFormatter, T


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
        messages: list[dict[str, str]],
        **api_params: Any,
    ) -> list[Any]:
        response = cls.get().chat.completions.create(
            model=model,
            messages=messages,
            **api_params,
        )
        if not hasattr(response, "choices") or not response.choices:
            raise ValueError("No choices returned from the model")
        return response.choices


def _get_messages(prompt_ret: str | list[dict[str, str]], prompt: Callable) -> list[dict[str, str]]:
    """
    获取消息列表，用于模型推理。

    :param prompt_ret: 提示函数的返回值，可以是字符串或消息列表
    :param prompt: 提示函数
    :return: 返回消息列表
    """
    if isinstance(prompt_ret, str):
        messages = []
        if prompt.__doc__ and prompt.__doc__.strip():
            messages.append({"role": "system", "content": prompt.__doc__})
        messages.append({"role": "user", "content": prompt_ret})
        return messages
    elif isinstance(prompt_ret, list):
        return prompt_ret
    else:
        raise TypeError("Expected prompt_ret to be a str or list of Messages")


def llm(
    model: str, **api_params: Any
) -> Callable[[Callable[..., str | T]], Callable[..., str | list[str] | T | list[T]]]:
    """
    LLM 装饰器，用于指定语言模型和其参数。

    :param model: 模型名称
    :param api_params: API 参数，以关键字参数形式传入
    :return: 返回一个装饰器，用于装饰提示函数
    """
    default_model_from_decorator = model
    default_api_params_from_decorator = api_params.copy()

    def parameterized_lm_decorator(prompt: Callable[..., str | T]) -> Callable[..., str | list[str] | T | list[T]]:
        """
        参数化的 LLM 装饰器，实际装饰提示函数。

        :param prompt: 提示函数，返回值可以是字符串或BaseModel的子类实例
        :return: 返回一个模型调用函数
        """

        @wraps(prompt)
        def model_call(
            *prompt_args: str | list[str],
            api_params: dict[str, Any] | None = None,
            **prompt_kwargs: str | list[str],
        ) -> str | list[str] | T | list[T]:
            """
            模型调用函数，实际执行模型推理。

            :param prompt_args: 提示函数的位置参数
            :param api_params: API 参数，覆盖装饰器级别的参数
            :param prompt_kwargs: 提示函数的关键字参数
            :return: 返回模型生成的文本或BaseModel的子类实例，可以是单个或列表
            """

            # 获取被修饰函数的返回类型
            response_format = ResponseFormatter[T](prompt)

            # 合并装饰器级别的API参数和函数级别的API参数
            merged_api_params = config.default_api_params.copy()
            if default_api_params_from_decorator:
                merged_api_params.update(default_api_params_from_decorator)
            if api_params:
                merged_api_params.update(api_params)

            # 获取同时运行的次数
            n = merged_api_params.get("n", 1)
            # 获取模型名称
            model = merged_api_params.pop("model", default_model_from_decorator)

            # 验证 prompt_args 和 prompt_kwargs 中的列表长度是否一致
            list_lengths = [len(arg) for arg in prompt_args if isinstance(arg, list)]
            list_lengths += [len(value) for value in prompt_kwargs.values() if isinstance(value, list)]
            if len(set(list_lengths)) > 1:
                raise ValueError("prompt_args 和 prompt_kwargs 中的所有列表必须具有相同的长度")

            if list_lengths and list_lengths[0] > 1 and n > 1:
                raise ValueError("n > 1 和列表长度 > 1 不能同时成立")

            results = []
            for i in range(list_lengths[0] if list_lengths else 1):
                args = [arg[i] if isinstance(arg, list) else arg for arg in prompt_args]
                kwargs = {key: value[i] if isinstance(value, list) else value for key, value in prompt_kwargs.items()}
                res = cast(str | list, prompt(*args, **kwargs))
                messages = _get_messages(res, prompt)
                response_format.process_parameters(messages, merged_api_params, model)
                try:
                    response = Client.generate(
                        model,
                        messages,
                        **merged_api_params,
                    )
                except Exception as e:
                    raise RuntimeError(f"生成响应失败: {e}") from e
                results.extend([response_format.parse_from_response(choice) for choice in response])
            if len(results) <= 0:
                raise ValueError("模型未返回任何选择")
            if len(results) == 1:
                if n != 1:
                    raise ValueError("预期一个选择，但得到多个")
                return results[0]
            return results

        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        return model_call

    return parameterized_lm_decorator
