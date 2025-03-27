from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Sequence
from functools import wraps
from typing import Any, Literal, overload

from .config import config
from .llm import gen_prompt, llm
from .prompt import REACT_SYSTEM_PROMPT
from .react_action import Action
from .schema import Messages, P, T
from .session import Session
from .tool import MCP, Tool, Tools, convert_to_tools
from .utils import retry


@Tool.tool
def final_answer(answer: str) -> str:
    """When get Final Answer, use this tool to return the answer and finishes the task."""
    return answer


@overload
def react(
    model: str = "",
    tools: list[Tool | MCP | Tools] | None = None,
    *,
    response_format: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str]]: ...


@overload
def react(
    model: str = "",
    tools: list[Tool | MCP | Tools] | None = None,
    *,
    response_format: type[T],
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, T]]: ...


def react(
    model: str = "",
    tools: list[Tool | MCP | Tools] | None = None,
    *,
    response_format: type[T] | None = None,
    max_steps: int = -1,
    session: Session | None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str | T]]:
    default_model_from_decorator = model or config.default_model
    default_tools = convert_to_tools(tools)
    default_tools.append(final_answer)
    default_response_format = response_format  # noqa: F841
    default_api_params_from_decorator = api_params.copy()
    default_session = session or Session("react")
    default_session.model = default_model_from_decorator

    def parameterized_lm_decorator(
        prompt: Callable[P, str | Messages | None],
    ) -> Callable[P, str | T]:
        @wraps(prompt)
        def model_call(
            *prompt_args: P.args,
            **prompt_kwargs: P.kwargs,
        ) -> str | T:
            default_session.func = Session.format_func_call(prompt, *prompt_args, **prompt_kwargs)
            tool_names = [f"`{tool.name}`" for tool in default_tools]

            def react_once(*prompt_args: P.args, acts: Sequence[Action], **prompt_kwargs: P.kwargs):  # type: ignore
                message = gen_prompt(prompt, *prompt_args, **prompt_kwargs)
                if isinstance(message, list):
                    if acts:
                        message.append({"role": "assistant", "content": str(acts[-1])})
                    return message
                elif isinstance(message, str):
                    return message + "\n" + "\n".join(str(a) for a in acts) + "\n" + "Thought:"
                else:
                    raise ValueError("Invalid output type")

            react_once.__doc__ = REACT_SYSTEM_PROMPT.format(
                tool_names=", ".join(tool_names),
                tool_descriptions=_tool_descriptions(default_tools),
                extra_instructions=prompt.__doc__ if prompt.__doc__ else "",
                language=config.default_language,
            )

            @retry(n=config.llm_max_retry, timeout=config.llm_timeout, wait=config.llm_wait_time)
            def react_response_action_with_retry(*args: Any, **kwargs: Any) -> Action:
                result = llm(
                    model=default_model_from_decorator,
                    session=default_session,
                    map_keys=None,
                    response_format=None,
                    n=None,
                    tools=None,
                    stop=["Observation:"],
                    **default_api_params_from_decorator,
                )(react_once)(*args, **kwargs)
                if isinstance(result, Iterator):
                    result = "".join(result)
                act = Action.from_response(result)
                default_session.log("action", act.thought, style="yellow")
                return act

            def final_call(
                *prompt_args: P.args,
                acts: Sequence[Action],  # type: ignore
                call_type: Literal["failed", "trans"],  # type: ignore
                **prompt_kwargs: P.kwargs,
            ) -> str | Messages:
                system_prompt = (
                    "An agent attempted to solve the user's task but encountered difficulties and failed. Your task is to provide the final answer instead.\n"
                    if call_type == "failed"
                    else "An agent has completed the user's task and now needs to convert the final answer into a new output format.\n"
                )
                message = gen_prompt(prompt, *prompt_args, **prompt_kwargs)
                memory = "\n".join(str(a) for a in acts)
                if isinstance(message, list):
                    return [
                        {"role": "system", "content": system_prompt},
                        *message,
                        {"role": "assistant", "content": str(acts[-1])},
                        {
                            "role": "user",
                            "content": "Based on the information above, please provide a response to the user's request.",
                        },
                    ]
                elif isinstance(message, str):
                    return f"{system_prompt}\nHere is the agent's memory:\n-----{message}\n{memory}\n-----\n Based on the information above, please provide a response to the user's request."
                else:
                    raise ValueError("Invalid output type")

            llm_final_call = llm(
                default_model_from_decorator,
                response_format=default_response_format,
                session=default_session,
                map_keys=None,
                need_retry=True,
                n=None,
                tools=None,
                **default_api_params_from_decorator,
            )(final_call)

            default_session.show_base_info()

            react_times = 0
            acts: list[Action] = []
            act = Action()
            while react_times == 0 or not act.done and (max_steps == -1 or react_times < max_steps):
                react_times += 1
                default_session.log("rule", f"Step {react_times}", align="left")
                image = act.image  # 如果上次的结果中有图片
                act = react_response_action_with_retry(*prompt_args, image=image, acts=acts, **prompt_kwargs)
                default_session.process(act)  # 工具执行
                acts.append(act)

            response: str | Iterator[str] | T = act.obs
            if not act.done and react_times == max_steps:
                response = llm_final_call(*prompt_args, acts=acts, call_type="failed", **prompt_kwargs)
            elif default_response_format is not None:
                response = llm_final_call(*prompt_args, acts=acts, call_type="trans", **prompt_kwargs)
            if isinstance(response, Iterator):
                response = "".join(response)
            return response

        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        return model_call

    return parameterized_lm_decorator


def _tool_descriptions(tools: list[Tool]) -> str:
    descriptions = []

    for tool in tools:
        markdown = f"### {tool.name}\n"
        markdown += f"> {tool.description}\n\n"
        markdown += f"{json.dumps(tool.args_schema, ensure_ascii=False)}\n"
        descriptions.append(markdown)
    return "\n".join(descriptions)
