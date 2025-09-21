"""
llm模块提供了与大型语言模型（LLM）交互的核心功能。
它包含一个装饰器，用于将函数转换为LLM调用，支持多种模型、参数配置、
响应格式化、并行处理和流式响应。
"""

from __future__ import annotations

import inspect  # 导入inspect模块，用于检查函数签名
from collections.abc import Callable, Iterable, Iterator  # 导入各种抽象基类，用于类型提示
from concurrent.futures import ThreadPoolExecutor, as_completed  # 导入线程池和完成状态，用于并行处理
from functools import wraps  # 导入wraps，用于保留被装饰函数的元数据
from typing import Any, overload  # 导入Any和overload，用于类型提示

from .client import SUPPORT_MULTIMODAL_MODELS, Client  # 从当前包导入Client和SUPPORT_MULTIMODAL_MODELS
from .config import config  # 从当前包导入配置
from .schema import Messages, P, T, ToolResponse  # 从当前包导入Messages、P、T和ToolResponse
from .session import Session  # 从当前包导入Session
from .structured import ResponseModel  # 从当前包导入ResponseModel
from .utils import Stream, retry  # 从当前包导入Stream和retry工具


# 以下是llm装饰器的多个重载定义，用于支持不同的参数组合和返回类型
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

    这是一个功能强大的装饰器，可以将普通函数转换为LLM调用。它支持多种参数配置，
    包括模型选择、响应格式、并行处理、重试机制等。

    Args:
        func_or_model: 可以是要装饰的函数或模型名称
        model: 模型名称，如 "openai:gpt-4o"
        map_keys: 用于批量处理的参数键列表
        response_format: 响应格式类型，用于结构化输出
        session: 会话对象，用于跟踪对话状态
        need_retry: 是否启用重试机制
        **api_params: 传递给LLM API的额外参数

    Returns:
        装饰器函数或已装饰的函数
    """
    if isinstance(func_or_model, str):
        model = func_or_model
        func = None
    elif callable(func_or_model):
        func = func_or_model
    else:
        func = None
    default_model_from_decorator = model  # 从装饰器获取的默认模型
    default_session = session or Session()  # 创建或使用传入的会话
    default_api_params_from_decorator = api_params.copy()  # 复制装饰器级别的API参数

    def parameterized_lm_decorator(
        prompt: Callable[P, str | Messages | None],
    ) -> Callable[P, str | ToolResponse | T | list[str] | list[ToolResponse] | list[T]]:
        """
        参数化的LLM装饰器，负责实际的函数装饰逻辑。

        Args:
            prompt: 要装饰的提示函数

        Returns:
            装饰后的函数
        """

        @wraps(prompt)
        def model_call(
            *prompt_args: P.args,
            image: str | list[str] | None = None,  # type: ignore # 图像输入，支持URL或base64
            api_params: dict[str, Any] | None = None,  # type: ignore # 函数级别的API参数
            **prompt_kwargs: P.kwargs,
        ) -> str | Iterator[str] | ToolResponse | T | list[str] | list[ToolResponse] | list[T]:
            # 格式化函数调用信息用于会话记录
            default_session.func = Session.format_func_call(prompt, *prompt_args, **prompt_kwargs)
            # 获取被修饰函数的返回类型
            response_model = ResponseModel[T](prompt, response_format)

            # 合并装饰器级别的API参数和函数级别的API参数
            merged_api_params = config.default_api_params.copy()  # 从配置获取默认参数
            if "tools" in merged_api_params:
                merged_api_params.pop("tools")  # 移除tools参数，避免冲突
            if default_api_params_from_decorator:
                merged_api_params.update(default_api_params_from_decorator)  # 更新装饰器参数
            if api_params:
                if "tools" in api_params:
                    api_params.pop("tools")  # 移除tools参数
                merged_api_params.update(api_params)  # 更新函数级别参数

            # 获取同时运行的次数
            n = merged_api_params.get("n", 1)
            if n is None:
                n = 1
            # 获取模型名称
            model = merged_api_params.pop("model", default_model_from_decorator) or config.default_model
            if model not in SUPPORT_MULTIMODAL_MODELS:
                image = None  # 如果模型不支持多模态，则清空图像参数
            default_session.model = model
            default_session.show_base_info()  # 显示基础信息

            # 获取映射键信息，用于批量处理
            m, map_args_index_set, map_kwargs_keys_set = _get_map_keys(prompt, prompt_args, prompt_kwargs, map_keys)
            if m > 1 and n > 1:
                raise ValueError("n > 1 和列表长度 > 1 不能同时成立")
            if (m > 1 or n > 1) and merged_api_params.get("stream", False):
                raise ValueError("stream 不能与列表长度 > 1 同时成立")

            def process_single_prompt(i: int) -> Iterable[Any]:
                """
                处理单个提示的内部函数。

                Args:
                    i: 批处理索引

                Returns:
                    处理结果的迭代器
                """
                # 根据映射键索引获取对应的参数
                args = [arg[i] if j in map_args_index_set else arg for j, arg in enumerate(prompt_args)]  # type: ignore
                kwargs = {
                    key: value[i] if key in map_kwargs_keys_set else value  # type: ignore
                    for key, value in prompt_kwargs.items()
                }
                # 生成提示内容
                res = gen_prompt(prompt, *args, **kwargs)
                assert (
                    isinstance(res, str) or isinstance(res, list) and all(isinstance(item, dict) for item in res)
                ), ValueError("被修饰的函数返回值必须是 str 或 `messages`(list[dict[str, str]]) 类型")
                # 生成消息格式
                messages = _gen_messages(res, prompt, image)
                # 处理响应模型参数
                response_model.process_parameters(model, messages, merged_api_params)

                # 发送API参数和消息到会话
                default_session.send("api_params", merged_api_params)
                default_session.send(
                    "messages", messages, id=default_session.id, session_type=default_session.session_type
                )

                # 调用客户端生成响应
                response = Client.generate(model, messages, **merged_api_params)

                if merged_api_params.get("stream", False):
                    # 处理流式响应
                    stream = Stream(process_stream_resopnse(response))
                    default_session.send("results", stream)
                    return stream.iterator
                else:
                    # 处理普通响应
                    result = [response_model.parse_from_response(choice) for choice in response]
                    default_session.send("progress_intermediate")
                    default_session.send("results", result)
                    return result

            results: list[str] | list[ToolResponse] | list[T] = []

            # 发送进度开始信号
            default_session.send("progress_start", m if m > 1 else n)

            if merged_api_params.get("stream", False):
                # 返回流式响应的生成器
                return (item for item in process_single_prompt(0) if isinstance(item, str) and item)

            if config.use_parallel_processing:
                # 使用并行处理
                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(process_single_prompt, i) for i in range(m)]

                    for future in as_completed(futures):
                        results.extend(future.result())
            else:
                # 串行处理
                for i in range(m):
                    results.extend(process_single_prompt(i))

            # 发送进度结束信号
            default_session.send("progress_end")

            if not results:
                raise ValueError("模型未返回任何选择")
            return (
                results if "n" in merged_api_params and merged_api_params["n"] is not None or map_keys else results[0]
            )

        # 添加元数据到装饰后的函数
        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        if need_retry:
            # 如果需要重试，则包装重试逻辑
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
    """
    获取映射键信息，用于批量处理。

    Args:
        prompt: 提示函数
        prompt_args: 位置参数
        prompt_kwargs: 关键字参数
        map_keys: 映射键列表

    Returns:
        包含批处理数量、位置参数索引集合、关键字参数键集合的元组
    """
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
    """
    生成消息格式，用于LLM API调用。

    Args:
        prompt_ret: 提示函数的返回值（字符串或消息列表）
        prompt: 提示函数
        image: 图像输入（可选）

    Returns:
        格式化的消息列表

    Raises:
        TypeError: 当prompt_ret不是预期的类型时
    """
    if isinstance(prompt_ret, str) and prompt_ret:
        messages: Messages = []
        # 如果函数有文档字符串，将其作为系统消息
        if prompt.__doc__ and prompt.__doc__.strip():
            messages.append({"role": "system", "content": prompt.__doc__})

        # 生成用户消息内容
        content = _gen_content(prompt_ret)
        if image:
            # 处理图像输入
            images = image if isinstance(image, list) else [image]
            for _image in images:
                if _image.startswith("http://") or _image.startswith("https://"):
                    # 处理URL图像
                    content.append({"type": "image_url", "image_url": {"url": _image}})
                else:
                    # 处理base64图像
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_image}"}})
        messages.append({"role": "user", "content": content})
        return messages
    if isinstance(prompt_ret, list) and prompt_ret:
        messages = prompt_ret
        # 如果消息列表没有系统消息且函数有文档字符串，则添加系统消息
        if (not messages or messages[0]["role"] != "system") and prompt.__doc__ and prompt.__doc__.strip():
            messages.insert(0, {"role": "system", "content": prompt.__doc__})
        return messages
    else:
        raise TypeError("Expected prompt_ret to be a str or list of Messages and not empty")


def _gen_content(text: str) -> list[dict[str, Any]]:
    """
    生成文本内容格式。

    Args:
        text: 文本内容

    Returns:
        格式化的内容列表
    """
    return [{"type": "text", "text": text}]


def gen_prompt(prompt: Callable[P, str | Messages | None], *args: Any, **kwargs: Any) -> str | Messages:
    """
    生成提示内容。

    如果提示函数返回值不为None，则直接返回该值。
    否则，根据函数参数自动生成XML格式的提示内容。

    Args:
        prompt: 提示函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        生成的提示内容（字符串或消息列表）
    """
    output = prompt(*args, **kwargs)
    if output is not None:
        return output

    # 自动生成提示内容
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
    """
    处理流式响应，特别处理推理内容（reasoning content）。

    该函数会检测响应中的推理内容，并自动添加<thinking>标签包装。

    Args:
        response: 来自LLM的流式响应

    Yields:
        处理后的响应内容字符串
    """
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
