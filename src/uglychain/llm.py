from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from typing import Any, overload

from .client import SUPPORT_MULTIMODAL_MODELS, Client
from .config import config
from .schema import Messages, P, T, ToolResponse
from .session import Session
from .structured import ResponseModel
from .utils import retry


@overload
def llm(
    func: Callable[P, str | Messages | None],
    /,
) -> Callable[P, str]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: None = None,
    response_format: None = None,
    n: None = None,
    tools: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str | Iterator[str]]]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: None = None,
    response_format: None = None,
    n: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str | Iterator[str] | ToolResponse]]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: None = None,
    response_format: None = None,
    n: int,
    tools: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[str]]]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: None = None,
    response_format: None = None,
    n: int,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[str] | list[ToolResponse]]]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: None = None,
    response_format: type[T],
    n: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, T]]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: None = None,
    response_format: type[T],
    n: int,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[T]]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: None = None,
    response_format: None = None,
    n: None = None,
    tools: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str | Iterator[str]]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: None = None,
    response_format: None = None,
    n: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str | Iterator[str] | ToolResponse]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: None = None,
    response_format: type[T],
    n: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, T]]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: list[str],
    response_format: None = None,
    tools: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[str]]]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: list[str],
    response_format: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[str] | list[ToolResponse]]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: None = None,
    response_format: None = None,
    n: int,
    tools: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[str]]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: None = None,
    response_format: None = None,
    n: int,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[str] | list[ToolResponse]]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: list[str],
    response_format: None = None,
    tools: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[str]]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: list[str],
    response_format: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[str] | list[ToolResponse]]]: ...


@overload
def llm(
    model: str,
    /,
    *,
    map_keys: list[str],
    response_format: type[T],
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[T]]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: None = None,
    response_format: type[T],
    n: int,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[T]]]: ...


@overload
def llm(
    *,
    model: str = "",
    map_keys: list[str],
    response_format: type[T],
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, list[T]]]: ...


def llm(
    func_or_model: Callable[P, str | Messages | None] | str | None = None,
    /,
    *,
    model: str = "",
    map_keys: list[str] | None = None,
    response_format: type[T] | None = None,
    session: Session | None = None,
    need_retry: bool = False,
    **api_params: Any,
) -> (
    Callable[P, str]
    | Callable[
        [Callable[P, str | Messages | None]],
        Callable[P, str | Iterator[str] | ToolResponse | T | list[str] | list[ToolResponse] | list[T]],
    ]
):
    """
    LLM 装饰器，用于指定语言模型和其参数。

    :param model: 模型名称
    :param api_params: API 参数，以关键字参数形式传入
    :return: 返回一个装饰器，用于装饰提示函数
    """
    if isinstance(func_or_model, str):
        model = func_or_model
        func = None
    elif callable(func_or_model):
        func = func_or_model
    else:
        func = None
    default_model_from_decorator = model
    default_session = session or Session()
    default_api_params_from_decorator = api_params.copy()

    def parameterized_lm_decorator(
        prompt: Callable[P, str | Messages | None],
    ) -> Callable[P, str | ToolResponse | T | list[str] | list[ToolResponse] | list[T]]:
        @wraps(prompt)
        def model_call(
            *prompt_args: P.args,
            image: str | list[str] | None = None,  # type: ignore
            api_params: dict[str, Any] | None = None,  # type: ignore
            **prompt_kwargs: P.kwargs,
        ) -> str | Iterator[str] | ToolResponse | T | list[str] | list[ToolResponse] | list[T]:
            default_session.func = Session.format_func_call(prompt, *prompt_args, **prompt_kwargs)
            # 获取被修饰函数的返回类型
            response_model = ResponseModel[T](prompt, response_format)

            # 合并装饰器级别的API参数和函数级别的API参数
            merged_api_params = config.default_api_params.copy()
            if "tools" in merged_api_params:
                merged_api_params.pop("tools")
            if default_api_params_from_decorator:
                merged_api_params.update(default_api_params_from_decorator)
            if api_params:
                if "tools" in api_params:
                    api_params.pop("tools")
                merged_api_params.update(api_params)

            # 获取同时运行的次数
            n = merged_api_params.get("n", 1)
            if n is None:
                n = 1
            # 获取模型名称
            model = merged_api_params.pop("model", default_model_from_decorator) or config.default_model
            if model not in SUPPORT_MULTIMODAL_MODELS:
                image = None
            default_session.model = model
            default_session.show_base_info()

            m, map_args_index_set, map_kwargs_keys_set = _get_map_keys(prompt, prompt_args, prompt_kwargs, map_keys)
            if m > 1 and n > 1:
                raise ValueError("n > 1 和列表长度 > 1 不能同时成立")
            if (m > 1 or n > 1) and merged_api_params.get("stream", False):
                raise ValueError("stream 不能与列表长度 > 1 同时成立")

            def process_single_prompt(i: int) -> Iterable[Any]:
                args = [arg[i] if j in map_args_index_set else arg for j, arg in enumerate(prompt_args)]  # type: ignore
                kwargs = {
                    key: value[i] if key in map_kwargs_keys_set else value  # type: ignore
                    for key, value in prompt_kwargs.items()
                }
                res = gen_prompt(prompt, *args, **kwargs)
                assert (
                    isinstance(res, str) or isinstance(res, list) and all(isinstance(item, dict) for item in res)
                ), ValueError("被修饰的函数返回值必须是 str 或 `messages`(list[dict[str, str]]) 类型")
                messages = _gen_messages(res, prompt, image)
                response_model.process_parameters(model, messages, merged_api_params)

                default_session.log("api_params", api_params=merged_api_params)
                default_session.log("messages", messages=messages)

                response = Client.generate(model, messages, **merged_api_params)

                if merged_api_params.get("stream", False):
                    return process_stream_resopnse(response)
                else:
                    result = [response_model.parse_from_response(choice) for choice in response]
                    default_session.log("progress_intermediate")
                    default_session.log("results", result=result)
                    return result

            results: list[str] | list[ToolResponse] | list[T] = []

            default_session.log("progress_start", n=m if m > 1 else n)

            if merged_api_params.get("stream", False):
                return (item for item in process_single_prompt(0) if isinstance(item, str) and item)
            if config.use_parallel_processing:
                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(process_single_prompt, i) for i in range(m)]

                    for future in as_completed(futures):
                        results.extend(future.result())
            else:
                for i in range(m):
                    results.extend(process_single_prompt(i))

            default_session.log("progress_end")

            if not results:
                raise ValueError("模型未返回任何选择")
            return (
                results if "n" in merged_api_params and merged_api_params["n"] is not None or map_keys else results[0]
            )

        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        if need_retry:
            return retry(n=config.llm_max_retry, timeout=config.llm_timeout, wait=config.llm_wait_time)(model_call)  # type: ignore
        else:
            return model_call  # type: ignore

    # 检查是否直接应用装饰器而不是传递参数
    if func is not None:
        return parameterized_lm_decorator(func)  # type: ignore

    return parameterized_lm_decorator


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


def _gen_messages(prompt_ret: str | Messages, prompt: Callable, image: str | list[str] | None = None) -> Messages:
    if isinstance(prompt_ret, str) and prompt_ret:
        messages: Messages = []
        if prompt.__doc__ and prompt.__doc__.strip():
            messages.append({"role": "system", "content": prompt.__doc__})

        content = _gen_content(prompt_ret)
        if image:
            images = image if isinstance(image, list) else [image]
            for _image in images:
                if _image.startswith("http://") or _image.startswith("https://"):
                    content.append({"type": "image_url", "image_url": {"url": _image}})
                else:
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_image}"}})
        messages.append({"role": "user", "content": content})
        return messages
    if isinstance(prompt_ret, list) and prompt_ret:
        messages = prompt_ret
        if (not messages or messages[0]["role"] != "system") and prompt.__doc__ and prompt.__doc__.strip():
            messages.insert(0, {"role": "system", "content": prompt.__doc__})
        return messages
    else:
        raise TypeError("Expected prompt_ret to be a str or list of Messages and not empty")


def _gen_content(text: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": text}]


def gen_prompt(prompt: Callable[P, str | Messages | None], *args: Any, **kwargs: Any) -> str | Messages:
    output = prompt(*args, **kwargs)
    if output is not None:
        return output
    signature = inspect.signature(prompt)
    bound_arguments = signature.bind(*args, **kwargs)
    bound_arguments.apply_defaults()
    segments: list[str] = []
    for name, value in bound_arguments.arguments.items():
        if not value:
            continue
        elif isinstance(value, str):
            segments.append(f"<{name}>\n{value}\n</{name}>")
        else:
            segments.append(f"<{name}>\n{value!r}\n</{name}>")
    return "\n".join(segments)


def process_stream_resopnse(response: Iterable) -> Iterator[str]:
    in_thinking = False
    for chunk in response:
        # 检查当前chunk是否有reasoning_content
        has_reasoning = hasattr(chunk.delta, "reasoning_content") and chunk.delta.reasoning_content
        content = chunk.delta.reasoning_content if has_reasoning else chunk.delta.content

        # 处理标签逻辑
        if has_reasoning:
            if not in_thinking:  # 进入thinking块
                yield "<thinking>\n"
                in_thinking = True
            yield content  # 输出内容
        else:
            if in_thinking:  # 离开thinking块
                yield "\n</thinking>\n"
                in_thinking = False
            yield content  # 输出普通内容

    # 流结束后闭合未关闭的标签
    if in_thinking:
        yield "\n</thinking>\n"
