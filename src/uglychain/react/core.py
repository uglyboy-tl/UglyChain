from __future__ import annotations

from collections.abc import Callable, Iterator
from functools import wraps
from typing import Any, overload

from uglychain.config import config
from uglychain.schema import Messages, P, T
from uglychain.session import Session
from uglychain.tools import Tool, Tools, convert_to_tool_list, final_answer

from .action import Action
from .base import BaseReActProcess
from .get_process import get_react_process


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
    process: BaseReActProcess = get_react_process(
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
                default_session.send("rule", f"Step {react_times}")
                image = act.image  # 如果上次的结果中有图片
                act = process.react(*prompt_args, image=image, acts=acts, **prompt_kwargs)
                process_act(default_session, act)  # 工具执行
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


def process_act(session: Session, act: Action) -> None:
    session.send("tool", act.tool, arguments=act.args)
    if not session.call_tool_confirm(act.tool):
        act.obs = "User cancelled. Please find other ways to solve this problem."
        return
    try:
        result = Tool.call_tool(act.tool, **act.args)
        act.obs, act.image = result if isinstance(result, tuple) else (result, None)
        session.send("action", _short_result(act.obs), style="bold green")
    except Exception as e:
        act.obs = f"Error: {e}"
        session.send("action", act.obs, style="bold red")


def _short_result(result: str) -> str:
    lines = result.split("\n")
    if len(lines) > 10:
        return "\n".join(lines[:10]) + "\n..."
    elif len(result) > 200:
        return result[:200] + "..."
    else:
        return result
