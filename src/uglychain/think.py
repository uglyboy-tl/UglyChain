"""
think模块提供思维链（Chain-of-Thought）功能。

该模块实现了一个装饰器，使用一个思考模型生成推理过程，
然后将该推理传递给响应模型生成最终答案。
"""

from __future__ import annotations

from collections.abc import Callable, Iterator  # 用于类型提示
from functools import wraps  # 用于保留被装饰函数的元数据
from typing import Any, overload  # 用于函数重载和类型提示

from .config import config  # 导入配置
from .llm import llm  # 导入LLM装饰器
from .schema import Messages, P, T  # 导入类型定义
from .session import Session  # 导入会话管理


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
    思维链装饰器，使用思考模型生成推理过程，然后将推理传递给响应模型生成最终答案。

    Args:
        model: 用于生成最终响应的模型
        thinking_model: 用于推理的模型（默认使用推理器模型）
        response_format: 可选的结构化输出类型
        session: 可选的会话对象，用于跟踪
        **api_params: 传递给模型的额外参数
    """
    default_session = session or Session("think")  # 创建或使用会话
    thinking_model = thinking_model or "deepseek:deepseek-reasoner"  # 默认使用deepseek推理器
    response_model = model or config.default_model  # 使用指定模型或默认模型
    default_api_params_from_decorator = api_params.copy()  # 复制API参数

    def decorator(func: Callable[P, str | Messages | None]) -> Callable[P, str | T]:
        """装饰器函数，包装原始函数"""

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> str | T:
            """包装函数，实现思维链逻辑"""
            # 移除不适用于思考模型的参数
            for key in ["map_keys", "tools", "n"]:
                if key in default_api_params_from_decorator:
                    default_api_params_from_decorator.pop(key)

            # 首先，使用思考模型生成推理过程
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
            reasoning = _get_reasoning(response)  # 从响应中提取推理内容

            # 然后，使用响应模型生成最终答案，包含推理过程
            @llm(
                model=response_model,
                response_format=response_format,
                session=default_session,
                **default_api_params_from_decorator,
            )
            def generate_response(*inner_args: Any, reasoning: str, **inner_kwargs: Any) -> str:
                """生成最终响应的内部函数"""
                prompt = func(*inner_args, **inner_kwargs)
                return f"{prompt}\n\n<reasoning>\n{reasoning}\n</reasoning>"

            return generate_response(*args, reasoning=reasoning, **kwargs)

        return wrapper

    return decorator


def _get_reasoning(raw_reasoning: Iterator[str]) -> str:
    """
    从原始推理响应中提取思考内容。

    通过流式处理方式寻找<thinking>标签之间的内容。

    Args:
        raw_reasoning: 原始推理响应的迭代器

    Returns:
        str: 提取的推理内容
    """
    # 定义标签
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
