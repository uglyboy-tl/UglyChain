from __future__ import annotations

from collections.abc import Callable, Iterator
from functools import wraps
from typing import Any, overload

from .config import config
from .llm import llm
from .schema import Messages, P, T
from .session import Session


@overload
def think(
    model: str = "",
    thinking_model: str = "",
    *,
    response_format: type[T],
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, T]]: ...


@overload
def think(
    model: str = "",
    thinking_model: str = "",
    *,
    response_format: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str]]: ...


def think(
    model: str = "",
    thinking_model: str = "",
    *,
    response_format: type[T] | None = None,
    session: Session | None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str | T]]:
    """
    A decorator that uses a thinking model to generate reasoning,
    then passes that reasoning to a response model for the final answer.

    Args:
        model: The model to use for the final response
        thinking_model: The model to use for reasoning (defaults to a reasoner model)
        response_format: Optional type for structured output
        session: Optional session for tracking
        **api_params: Additional parameters to pass to the models
    """
    default_session = session or Session("think")
    thinking_model = thinking_model or "deepseek:deepseek-reasoner"
    response_model = model or config.default_model
    default_api_params_from_decorator = api_params.copy()

    def decorator(func: Callable[P, str | Messages | None]) -> Callable[P, str | T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> str | T:
            # Remove any parameters that are not applicable to the thinking model
            for key in ["map_keys", "tools", "n"]:
                if key in default_api_params_from_decorator:
                    default_api_params_from_decorator.pop(key)
            # First, use the thinking model to generate reasoning
            generate_reasoning = llm(
                thinking_model,
                session=default_session,
                n=None,
                map_keys=None,
                stream=True,
                tools=None,
                **default_api_params_from_decorator,
            )(func)

            response: Iterator[str] = generate_reasoning(*args, **kwargs)
            reasoning = _get_reasoning(response)

            # Then, use the response model with the reasoning included
            @llm(
                model=response_model,
                response_format=response_format,
                session=default_session,
                **default_api_params_from_decorator,
            )
            def generate_response(*inner_args: Any, reasoning: str, **inner_kwargs: Any) -> str:
                """You are a helpful assistant. Use the provided reasoning to formulate your response."""
                prompt = func(*inner_args, **inner_kwargs)
                return f"{prompt}\n\n<reasoning>\n{reasoning}\n</reasoning>"

            return generate_response(*args, reasoning=reasoning, **kwargs)

        return wrapper

    return decorator


def _get_reasoning(raw_reasoning: Iterator[str]) -> str:
    # 通过流式处理方式寻找标签
    start_tag = "<thinking>\n"
    end_tag = "\n</thinking>\n"

    # 状态变量
    found_start = False  # 是否找到开始标签
    reasoning_parts = []  # 收集的内容部分
    buffer = ""  # 缓冲区，用于检测标签

    for chunk in raw_reasoning:
        buffer += chunk

        # 如果还没有找到开始标签，则先寻找开始标签
        if not found_start:
            if start_tag in buffer:
                found_start = True
                # 提取开始标签后的内容
                buffer = buffer[buffer.find(start_tag) + len(start_tag) :]
            else:
                # 保留最后 10 个字符，以检测跨块的开始标签
                buffer = buffer[-10:] if len(buffer) > 10 else buffer
                continue  # 继续处理下一个块

        # 如果已经找到开始标签，则寻找结束标签
        if end_tag in buffer:
            # 找到结束标签，只保留结束标签之前的内容
            reasoning_parts.append(buffer[: buffer.find(end_tag)])
            break
        else:
            reasoning_parts.append(buffer)
            buffer = ""

    # 如果找到了开始标签但没有结束标签，则保留所有内容
    if found_start and buffer:
        reasoning_parts.append(buffer)

    # 如果没有找到开始标签，则不保留任何内容
    reasoning = "".join(reasoning_parts) if found_start else ""
    return reasoning
