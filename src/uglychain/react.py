from __future__ import annotations

from collections.abc import Callable, Iterator
from functools import wraps
from typing import Any, overload

from ._react import Action
from ._react.base import BaseReActProcess
from ._react.core import ReActProcess
from .config import config
from .schema import Messages, P, T
from .session import Session
from .tools import Tools, convert_to_tool_list, final_answer


@overload
def react(
    model: str = "",
    tools: Tools | None = None,
    *,
    response_format: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str]]: ...


@overload
def react(
    model: str = "",
    tools: Tools | None = None,
    *,
    response_format: type[T],
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, T]]: ...


def react(
    model: str = "",
    tools: Tools | None = None,
    *,
    response_format: type[T] | None = None,
    max_steps: int = -1,
    session: Session | None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str | T]]:
    default_session = session or Session("react")
    process: BaseReActProcess = ReActProcess(
        model=model or config.default_model,
        session=default_session,
        tools=convert_to_tool_list(tools),
        response_format=response_format,
        api_params=api_params.copy(),
    )
    process.tools.append(final_answer)
    default_session.model = process.model

    def parameterized_lm_decorator(
        prompt: Callable[P, str | Messages | None],
    ) -> Callable[P, str | T]:
        @wraps(prompt)
        def model_call(
            *prompt_args: P.args,
            **prompt_kwargs: P.kwargs,
        ) -> str | T:
            process.func = prompt
            default_session.func = Session.format_func_call(prompt, *prompt_args, **prompt_kwargs)
            default_session.show_base_info()

            react_times = 0
            acts: list[Action] = []
            act = Action()
            while react_times == 0 or not act.done and (max_steps == -1 or react_times < max_steps):
                react_times += 1
                default_session.log("rule", f"Step {react_times}", align="left")
                image = act.image  # 如果上次的结果中有图片
                act = process.react(*prompt_args, image=image, acts=acts, **prompt_kwargs)
                default_session.process(act)  # 工具执行
                acts.append(act)

            response: str | Iterator[str] | T = act.obs
            if not act.done and react_times == max_steps:
                response = process.final(*prompt_args, acts=acts, call_type="failed", **prompt_kwargs)
            elif process.response_format is not None:
                response = process.final(*prompt_args, acts=acts, call_type="trans", **prompt_kwargs)
            if isinstance(response, Iterator):
                response = "".join(response)
            return response

        model_call.__api_params__ = process.api_params  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        return model_call

    return parameterized_lm_decorator
