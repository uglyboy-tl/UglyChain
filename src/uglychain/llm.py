from __future__ import annotations

import inspect
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from typing import Any, cast

from .client import Client
from .config import config
from .logger import Logger
from .response_format import ResponseModel, T
from .tools import add_tools_to_parameters


def llm(
    model: str,
    tools: list[Callable] | None = None,
    response_format: type[T] | None = None,
    map_keys: list[str] | None = None,
    **api_params: Any,
) -> Callable[[Callable[..., str | list[dict[str, str]] | T]], Callable[..., str | list[str] | T | list[T]]]:
    """
    LLM 装饰器，用于指定语言模型和其参数。

    :param model: 模型名称
    :param api_params: API 参数，以关键字参数形式传入
    :return: 返回一个装饰器，用于装饰提示函数
    """
    default_model_from_decorator = model
    default_api_params_from_decorator = api_params.copy()

    def parameterized_lm_decorator(
        prompt: Callable[..., str | list[dict[str, str]] | T],
    ) -> Callable[..., str | list[str] | T | list[T]]:
        @wraps(prompt)
        def model_call(
            *prompt_args: Any,
            api_params: dict[str, Any] | None = None,
            **prompt_kwargs: Any,
        ) -> str | list[str] | T | list[T]:
            logger = Logger()
            # 获取被修饰函数的返回类型
            response_model = ResponseModel(prompt, response_format)
            # 使用工具时会忽略结构化输出模式
            if tools is not None:
                response_model.response_type = str

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

            logger.model_usage_logger_pre(model, prompt, prompt_args, prompt_kwargs)

            m, map_args_index_set, map_kwargs_keys_set = _get_map_keys(prompt, prompt_args, prompt_kwargs, map_keys)
            if m > 1 and n > 1:
                raise ValueError("n > 1 和列表长度 > 1 不能同时成立")

            def process_single_prompt(i: int) -> list[Any]:
                args = [arg[i] if j in map_args_index_set else arg for j, arg in enumerate(prompt_args)]
                kwargs = {
                    key: value[i] if key in map_kwargs_keys_set else value for key, value in prompt_kwargs.items()
                }
                res = prompt(*args, **kwargs)
                assert (
                    isinstance(res, str) or isinstance(res, list) and all(isinstance(item, dict) for item in res)
                ), ValueError("被修饰的函数返回值必须是 str 或 `messages`(list[dict[str, str]]) 类型")
                messages = _get_messages(res, prompt)
                response_model.process_parameters(model, messages, merged_api_params)
                add_tools_to_parameters(merged_api_params, tools)

                logger.model_usage_logger_post_info(messages, merged_api_params)

                response = Client.generate(model, messages, **merged_api_params)

                # 从响应中解析结果
                result = [response_model.parse_from_response(choice, tools is not None) for choice in response]
                logger.model_usage_logger_post_intermediate(result)
                return result

            results = []
            logger.model_usage_progress_start(m if m > 1 else n)

            if config.use_parallel_processing:
                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(process_single_prompt, i) for i in range(m)]

                    for future in as_completed(futures):
                        results.extend(future.result())
            else:
                for i in range(m):
                    results.extend(process_single_prompt(i))

            logger.model_usage_progress_end()

            if len(results) == 0:
                raise ValueError("模型未返回任何选择")
            elif m == n == len(results) == 1:
                return results[0]
            return results

        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        return model_call

    return parameterized_lm_decorator  # type: ignore[return-value]


def _get_map_keys(
    prompt: Callable, prompt_args: tuple, prompt_kwargs: dict, map_keys: list[str] | None
) -> tuple[int, set[int], set[str]]:
    if map_keys is None:
        return 1, set(), set()
    map_key_set: set[str] = set(map_keys)
    map_num_set: set[int] = set()
    param_mapping = inspect.getcallargs(prompt, *prompt_args, **prompt_kwargs)

    list_lengths = []
    for i, (param_name, arg_value) in enumerate(param_mapping.items()):
        if param_name in map_key_set:
            if not isinstance(arg_value, list):
                raise ValueError("map_key 必须是列表")
            if i < len(prompt_args):
                map_num_set.add(i)
                map_key_set.remove(param_name)
            list_lengths.append(len(arg_value))

    if not list_lengths:
        return 1, set(), set()

    unique_lengths = set(list_lengths)
    if len(unique_lengths) > 1:
        raise ValueError("prompt_args 和 prompt_kwargs 中的 map_key 列表必须具有相同的长度")

    return list_lengths[0], map_num_set, map_key_set


def _get_messages(prompt_ret: str | list[dict[str, str]], prompt: Callable) -> list[dict[str, str]]:
    if isinstance(prompt_ret, str):
        messages = []
        if prompt.__doc__ and prompt.__doc__.strip():
            messages.append({"role": "system", "content": prompt.__doc__})
        messages.append({"role": "user", "content": prompt_ret})
        return messages
    elif isinstance(prompt_ret, list):
        messages = prompt_ret
        if (not messages or messages[0]["role"] != "system") and prompt.__doc__ and prompt.__doc__.strip():
            messages.insert(0, {"role": "system", "content": prompt.__doc__})
        return messages
    else:
        raise TypeError("Expected prompt_ret to be a str or list of Messages")
