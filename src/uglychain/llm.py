from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast, get_type_hints

import aisuite
from pydantic import BaseModel

from .response_format import from_response, get_response_format_prompt

# 创建一个泛型变量，用于约束BaseModel的子类
T = TypeVar("T", str, BaseModel)

# 单例模式缓存 Client 实例
_client_instance = None


def get_client() -> aisuite.Client:
    global _client_instance
    if _client_instance is None:
        _client_instance = aisuite.Client()
    return _client_instance


def empty_client() -> None:
    global _client_instance
    _client_instance = None


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

            # prompt -> str
            res = cast(str | list, prompt(*prompt_args, **prompt_kwargs))
            # Convert prompt into messages
            messages = _get_messages(res, prompt)

            merged_api_params = default_api_params_from_decorator.copy()
            if api_params:
                merged_api_params.update(api_params)

            if not issubclass(return_type, str):
                # TODO: 可以选择用怎样的方式实现结构化输出，当前只实现了基于 Prompt 的方式
                system_message = messages[0]
                if system_message["role"] == "system":
                    system_message["content"] += "\n-----\n" + get_response_format_prompt(return_type)
                else:
                    system_message = {"role": "system", "content": get_response_format_prompt(return_type)}
                    messages.insert(0, system_message)

            n = merged_api_params.get("n", 1)
            response = get_client().chat.completions.create(
                model=merged_api_params.pop("model", default_model_from_decorator),
                messages=messages,
                **merged_api_params,
            )

            result = []
            for choice in response.choices:
                if return_type is str:
                    result.append(choice.message.content)
                elif issubclass(return_type, BaseModel):
                    result.append(from_response(return_type, choice.message.content))

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
