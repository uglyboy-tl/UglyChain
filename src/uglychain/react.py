from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, ParamSpec, cast

from pydantic import BaseModel, Field

from .llm import llm
from .response_format import T
from .tools import function_schema

P = ParamSpec("P")

FUNCTION_CALL_WITH_FINISH_PROMPT = """
You can use tools: [{tool_names}]

Respond with tool name and tool arguments to achieve the instruction. if you can respond directly, use the tool 'finish' to return the answer and finishes the task:
{tool_schema}
"""


@dataclass
class Action:
    thought: str
    action: str
    parameters: dict
    obs: str
    current: bool = True

    @property
    def done(self) -> bool:
        if self.action == "finish":
            return True
        else:
            return False

    def __str__(self) -> str:
        return self.info

    @property
    def info(self) -> str:
        if self.done:
            return f"Thought: {self.thought}\nAction: Finish\nObservation: {self.obs}"
        return (
            f"Thought: {self.thought}\nAction: {self.action}\nAction Input: {self.parameters}\nObservation: {self.obs}"
        )

    @classmethod
    def from_response(cls, response: ActionResopnse, tools: list[Callable]) -> Action:
        return cls(
            thought=response.thought,
            action=response.action.name,
            parameters=response.action.parameters,
            obs=run_function(tools, response.action),
        )


class FunctionCall(BaseModel):
    name: str = Field(..., description="tool name")
    parameters: dict = Field(..., description="tool arguments")


class ActionResopnse(BaseModel):
    thought: str = Field(..., description="Think step by step and explan why you need to use a tool")
    action: FunctionCall = Field(..., description="The action to take")


def finish(answer: str) -> str:
    """When get Final Answer, use this tool to return the answer and finishes the task.
    Args:
        answer (str): The response to return.
    """
    return answer


def tools_schema(tools: list[Callable]) -> list[dict[str, Any]]:
    tools_schema = []

    for tool in tools:
        tools_schema.append(function_schema(tool))
    return tools_schema


def run_function(tools: list[Callable[..., str]], response: FunctionCall) -> str:
    for tool in tools:
        if tool.__name__ == response.name:
            return tool(**response.parameters)
    raise ValueError(f"Can't find tool {response.name}")


def react(
    model: str,
    tools: list[Callable],
    response_format: type[T] | None = None,
    max_reacts: int = -1,
    **api_params: Any,
) -> Callable[[Callable[P, str | list[dict[str, str]] | T]], Callable[P, str | T]]:
    default_model_from_decorator = model
    default_response_format = response_format
    default_api_params_from_decorator = api_params.copy()

    def parameterized_lm_decorator(
        prompt: Callable[P, str | list[dict[str, str]] | T],
    ) -> Callable[P, str | T]:
        @wraps(prompt)
        def model_call(
            *prompt_args: P.args,
            api_params: dict[str, Any] | None = None,  # type: ignore
            **prompt_kwargs: P.kwargs,
        ) -> str | T:
            tools.insert(0, finish)

            def react(*prompt_args: P.args, acts: list[Action], **prompt_kwargs: P.kwargs):  # type: ignore
                output = prompt(*prompt_args, **prompt_kwargs)
                if isinstance(output, list):
                    output[-1]["content"] += "\n".join(str(a) for a in acts)
                elif isinstance(output, str):
                    return output + "\n".join(str(a) for a in acts)

            tool_names = ", ".join([f"`{tool.__name__}`" for tool in tools])
            react.__doc__ = (
                prompt.__doc__
                if prompt.__doc__
                else ""
                + FUNCTION_CALL_WITH_FINISH_PROMPT.format(
                    tool_names=tool_names, tool_schema=f"=====\n{tools_schema(tools)}\n====="
                )
            )

            llm_tool_call = llm(
                default_model_from_decorator,
                response_format=ActionResopnse,
                **default_api_params_from_decorator,
            )(react)  # type: ignore

            def final_call(*prompt_args: P.args, acts: list[Action], **prompt_kwargs: P.kwargs):  # type: ignore
                output = prompt(*prompt_args, **prompt_kwargs)
                history = "\n".join(str(a) for a in acts)
                if isinstance(output, list):
                    output[-1]["content"] += f"\n-----\n{history}\n-----\n Now you must give an final answer!"
                elif isinstance(output, str):
                    return output + f"\n-----\n{history}\n-----\n Now you must give an final answer!"

            llm_final_call = llm(
                default_model_from_decorator,
                response_format=default_response_format,
                **default_api_params_from_decorator,
            )(final_call)  # type: ignore
            acts: list[Action] = []
            react_times = 0
            result = cast(ActionResopnse, llm_tool_call(*prompt_args, acts=acts, **prompt_kwargs))
            act = Action.from_response(result, tools)
            while not act.done and (max_reacts == -1 or react_times < max_reacts):
                if acts:
                    acts[-1].current = False
                acts.append(act)
                result = cast(ActionResopnse, llm_tool_call(*prompt_args, acts=acts, **prompt_kwargs))
                act = Action.from_response(result, tools)
                print(act.info)
                react_times += 1
            response: str | T = act.obs
            if not act.done and react_times >= max_reacts or default_response_format is not None:
                response = llm_final_call(*prompt_args, acts=acts, **prompt_kwargs)  # type: ignore
            assert not isinstance(response, list)
            return response

        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        return model_call  # type: ignore

    return parameterized_lm_decorator  # type: ignore[return-value]
