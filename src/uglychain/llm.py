from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast, get_type_hints

import aisuite
from pydantic import BaseModel

from .response_format import ResponseFormatter

# 创建一个泛型变量，用于约束BaseModel的子类
T = TypeVar("T", str, BaseModel)

# 单例模式缓存 Client 实例
_client_instance = None


def get_client() -> aisuite.Client:
    """
    返回一个aisuite的Client实例。

    该函数使用了单例模式的设计原则，确保在整个应用程序中只有一个Client实例被创建和使用。
    这样做可以节省资源，并确保与Client的所有交互都是通过同一个实例进行的。

    Returns:
        aisuite.Client: aisuite的Client实例。
    """
    # 使用全局变量_client_instance来存储Client的唯一实例
    global _client_instance

    # 检查_client_instance是否已经初始化
    if _client_instance is None:
        # 如果尚未初始化，则创建一个新的Client实例并赋值给_client_instance
        _client_instance = aisuite.Client()

    # 返回Client实例
    return _client_instance


def empty_client() -> None:
    """
    将客户端实例重置为 None。

    该函数用于清除全局客户端实例变量，
    确保客户端状态在后续配置或使用前被重置。
    """
    global _client_instance  # 声明要修改的全局变量
    _client_instance = None  # 将客户端实例重置为 None


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


def _process_structured_with_parameters(
    messages: list[dict[str, str]], merged_api_params: dict[str, Any], return_type: type[BaseModel]
):
    # TODO: 可以选择用怎样的方式实现结构化输出，当前只实现了基于 Prompt 的方式
    system_message = messages[0]
    if system_message["role"] == "system":
        system_message["content"] += "\n-----\n" + ResponseFormatter.get_response_format_prompt(return_type)
    else:
        system_message = {
            "role": "system",
            "content": ResponseFormatter.get_response_format_prompt(return_type),
        }
        messages.insert(0, system_message)

    merged_api_params["response_format"] = {"type": "json_object"}


def llm(model: str, **api_params: Any) -> Callable[[Callable[..., T]], Callable[..., T | list[T]]]:
    """
    LLM 装饰器，用于指定语言模型和其参数。

    :param model: 模型名称
    :param api_params: API 参数，以关键字参数形式传入
    :return: 返回一个装饰器，用于装饰提示函数
    """
    # 存储装饰器级别的模型和API参数
    default_model_from_decorator = model
    default_api_params_from_decorator = api_params.copy()

    def parameterized_lm_decorator(prompt: Callable[..., T]) -> Callable[..., T | list[T]]:
        """
        参数化的 LLM 装饰器，实际装饰提示函数。

        :param prompt: 提示函数，返回值可以是字符串或BaseModel的子类实例
        :return: 返回一个模型调用函数
        """

        @wraps(prompt)
        def model_call(
            *prompt_args: str,
            api_params: dict[str, Any] | None = None,
            **prompt_kwargs: str,
        ) -> T | list[T]:
            """
            模型调用函数，实际执行模型推理。

            :param prompt_args: 提示函数的位置参数
            :param api_params: API 参数，覆盖装饰器级别的参数
            :param prompt_kwargs: 提示函数的关键字参数
            :return: 返回模型生成的文本或BaseModel的子类实例，可以是单个或列表
            """

            # 获取被修饰函数的返回类型
            return_type: type[str] | type[T] = get_type_hints(prompt).get("return", str)
            if return_type is not str and not issubclass(return_type, BaseModel):
                raise TypeError(f"Unsupported return type: {return_type}")

            # 获取提示函数的返回值
            res = cast(str | list, prompt(*prompt_args, **prompt_kwargs))
            # 获取提示函数的返回值对应的消息列表
            messages = _get_messages(res, prompt)

            # 合并装饰器级别的API参数和函数级别的API参数
            merged_api_params = default_api_params_from_decorator.copy()
            if api_params:
                merged_api_params.update(api_params)

            # 获取同时运行的次数
            n = merged_api_params.get("n", 1)

            # 处理结构化输出
            if not issubclass(return_type, str):
                _process_structured_with_parameters(messages, merged_api_params, return_type)

            # 调用模型
            response = get_client().chat.completions.create(
                model=merged_api_params.pop("model", default_model_from_decorator),
                messages=messages,
                **merged_api_params,
            )

            # 处理返回值
            result = []
            if return_type is str:
                for choice in response.choices:
                    result.append(choice.message.content)
            elif issubclass(return_type, BaseModel):
                for choice in response.choices:
                    result.append(ResponseFormatter.parse_model_from_response(return_type, choice.message.content))

            if len(result) <= 0:
                raise ValueError("No choices returned from the model")
            if len(result) == 1:
                if n != 1:
                    raise ValueError("Expected one choice but got multiple")
                return result[0]
            else:
                return result

        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        return model_call

    return parameterized_lm_decorator
