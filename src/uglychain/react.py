from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from functools import cached_property, wraps
from typing import Any, Generic, Literal, overload

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
    default_session = session or Session("react")
    process = ReActProcess(
        model=model or config.default_model,
        session=default_session,
        tools=convert_to_tools(tools),
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


@dataclass
class ReActProcess(Generic[T]):
    func: Callable[..., str | Messages | None] = field(init=False, default_factory=lambda: lambda *args, **kwargs: None)
    model: str
    session: Session
    tools: list[Tool]
    response_format: type[T] | None
    api_params: dict[str, Any]

    @cached_property
    def react(self) -> Callable[..., Action]:
        tools_names = [f"`{tool.name}`" for tool in self.tools]

        def react_once(*prompt_args: P.args, acts: Sequence[Action], **prompt_kwargs: P.kwargs):  # type: ignore
            message = gen_prompt(self.func, *prompt_args, **prompt_kwargs)
            if isinstance(message, list):
                if acts:
                    message.append({"role": "assistant", "content": str(acts[-1])})
                return message
            elif isinstance(message, str):
                return message + "\n" + "\n".join(str(a) for a in acts) + "\n" + "Thought:"
            else:
                raise ValueError("Invalid output type")

        react_once.__doc__ = REACT_SYSTEM_PROMPT.format(
            tools_names=", ".join(tools_names),
            tools_descriptions=self.tools_descriptions,
            extra_instructions=self.func.__doc__ if self.func.__doc__ else "",
            language=config.default_language,
        )

        @retry(n=config.llm_max_retry, timeout=config.llm_timeout, wait=config.llm_wait_time)
        def react_response_action_with_retry(*args: Any, **kwargs: Any) -> Action:
            result = llm(
                model=self.model,
                session=self.session,
                map_keys=None,
                response_format=None,
                n=None,
                tools=None,
                stop=["Observation:"],
                **self.api_params,
            )(react_once)(*args, **kwargs)
            if isinstance(result, Iterator):
                result = "".join(result)
            act = Action.from_response(result)
            self.session.log("action", act.thought, style="yellow")
            return act

        return react_response_action_with_retry

    @cached_property
    def final(self) -> Callable[..., str | Iterator[str] | T]:
        def final_call(
            *prompt_args: Any,
            acts: Sequence[Action],  # type: ignore
            call_type: Literal["failed", "trans"],  # type: ignore
            **prompt_kwargs: Any,
        ) -> str | Messages:
            system_prompt = (
                "An agent attempted to solve the user's task but encountered difficulties and failed. Your task is to provide the final answer instead.\n"
                if call_type == "failed"
                else "An agent has completed the user's task and now needs to convert the final answer into a new output format.\n"
            )
            message = gen_prompt(self.func, *prompt_args, **prompt_kwargs)
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
            self.model,
            response_format=self.response_format,
            session=self.session,
            map_keys=None,
            need_retry=True,
            n=None,
            tools=None,
            **self.api_params,
        )(final_call)

        return llm_final_call

    @cached_property
    def tools_descriptions(self) -> str:
        descriptions = []

        for tool in self.tools:
            markdown = f"### {tool.name}\n"
            markdown += f"> {tool.description}\n\n"
            markdown += f"{json.dumps(tool.args_schema, ensure_ascii=False)}\n"
            descriptions.append(markdown)
        return "\n".join(descriptions)
