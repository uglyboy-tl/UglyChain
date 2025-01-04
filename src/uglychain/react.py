from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, ParamSpec, cast

from .llm import llm
from .structured import T
from .tools import function_schema

P = ParamSpec("P")


def react(
    model: str,
    tools: list[Callable],
    response_format: type[T] | None = None,
    max_reacts: int = -1,
    **api_params: Any,
) -> Callable[[Callable[P, str | list[dict[str, str]] | T]], Callable[P, str | T]]:
    default_model_from_decorator = model
    default_response_format = response_format  # noqa: F841
    default_api_params_from_decorator = api_params.copy()

    def parameterized_lm_decorator(
        prompt: Callable[P, str | list[dict[str, str]] | T],
    ) -> Callable[P, str | T]:
        @wraps(prompt)
        def model_call(
            *prompt_args: P.args,
            **prompt_kwargs: P.kwargs,
        ) -> str | T:
            tools.insert(0, final_answer)

            def react(*prompt_args: P.args, acts: list[Action], **prompt_kwargs: P.kwargs):  # type: ignore
                output = prompt(*prompt_args, **prompt_kwargs)
                if isinstance(output, list):
                    output[-1]["content"] += "\n".join(str(a) for a in acts)
                elif isinstance(output, str):
                    return output + "\n".join(str(a) for a in acts)

            tool_names = ", ".join([f"`{tool.__name__}`" for tool in tools])
            react.__doc__ = (prompt.__doc__ if prompt.__doc__ else "") + SYSTEM_PROMPT.format(
                tool_names=tool_names, tool_descriptions=_tool_descriptions(tools)
            )

            llm_tool_call: Callable = llm(
                default_model_from_decorator,
                stop=["Observation:"],
                **default_api_params_from_decorator,
            )(react)

            def final_call(*prompt_args: P.args, acts: list[Action], **prompt_kwargs: P.kwargs):  # type: ignore
                output = prompt(*prompt_args, **prompt_kwargs)
                history = "\n".join(str(a) for a in acts)
                if isinstance(output, list):
                    output[-1]["content"] += f"\n-----{history}\n-----\n Now you must give an final answer!"
                elif isinstance(output, str):
                    return output + f"\n-----{history}\n-----\n Now you must give an final answer!"

            llm_final_call = llm(
                default_model_from_decorator,
                response_format=default_response_format,
                **default_api_params_from_decorator,
            )(final_call)  # type: ignore

            acts: list[Action] = []
            react_times = 0
            result = llm_tool_call(*prompt_args, acts=acts, **prompt_kwargs)
            assert isinstance(result, str)
            act = Action.from_response(result, tools)
            while not act.done and (max_reacts == -1 or react_times < max_reacts):
                if acts:
                    acts[-1].current = False
                acts.append(act)
                result = cast(str, llm_tool_call(*prompt_args, acts=acts, **prompt_kwargs))
                act = Action.from_response(result, tools)
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


SYSTEM_PROMPT = """You are an expert assistant who can solve any task using code blobs. You will be given a task to solve as best you can.
To do so, you have been given access to a list of tools: [{tool_names}].
To solve the task, you must plan forward to proceed in a series of steps, in a cycle of 'Thought:', 'Action:', 'Action Input:', and 'Observation:' sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning towards solving the task and the tools that you want to use.
Then in the 'Action:' and 'Action Input:' sequence, you should tell system what tool to use and what arguments to use.
The action result will then appear in the 'Observation:' field, which will be available as input for the next step. And you do not need to generate this part, it will be automatically filled by the system.
In the end you have to return a final answer using the `final_answer` tool.

An fake example:
```
Task:
the input question you must answer

Thought: you should always think about what to do
Action: the action to take, should be one of tools
Action Input: the input to the action with JSON format representing the kwargs (e.g. {{"text": "hello world", "num_beams": 5}})
Observation: the result of the action

... (this Thought/Action/Action Input/Observation can be repeated zero or more times)

Thought: I now know the final answer
Action: final_answer
Action Input: {{"answer":"<answer>"}}
```
Tools:
{tool_descriptions}
"""


def _run_function(tools: list[Callable[..., str]], name: str, args: dict) -> str:
    for tool in tools:
        if tool.__name__ == name:
            return tool(**args)
    raise ValueError(f"Can't find tool {name}")


def final_answer(answer: str) -> str:
    """When get Final Answer, use this tool to return the answer and finishes the task."""
    return answer


@dataclass
class Action:
    thought: str
    tool: str
    args: dict
    obs: str
    current: bool = True

    @property
    def done(self) -> bool:
        if self.tool == "final_answer":
            return True
        else:
            return False

    def __str__(self) -> str:
        return self.info

    @property
    def info(self) -> str:
        if self.done:
            return f"\nThought: {self.thought}\nAction: Finish\nObservation: {self.obs}"
        return f"\nThought: {self.thought}\nAction: {self.tool}\nAction Input: {self.args}\nObservation: {self.obs}"

    @classmethod
    def from_response(cls, text: str, tools: list[Callable]) -> Action:
        special_func_token = "\nAction:"
        special_args_token = "\nAction Input:"
        special_obs_token = "\nObservation:"
        func_name, func_args = None, None
        i = text.rfind(special_func_token)
        j = text.rfind(special_args_token)
        k = text.rfind(special_obs_token)
        if 0 <= i < j:  # If the text has `Action` and `Action input`,
            if k < j:  # but does not contain `Observation`,
                # then it is likely that `Observation` is omitted by the LLM,
                # because the output text may have discarded the stop word.
                text = text.rstrip() + special_obs_token  # Add it back.
            k = text.rfind(special_obs_token)
            func_name = text[i + len(special_func_token) : j].strip()
            func_args = text[j + len(special_args_token) : k].strip()
            text = text[:i].strip()  # Return the response before tool call, i.e., `Thought`
            if text.startswith("Thought:"):
                text = text[len("Thought:") :]
        # return (func_name is not None), func_name, func_args, text
        if func_name is None or func_args is None:
            raise ValueError("Can't parse the response")
        tool = func_name
        args = json.loads(func_args)
        return cls(
            thought=text,
            tool=tool,
            args=args,
            obs=_run_function(tools, tool, args),
        )


def _tool_descriptions(tools: list[Callable]) -> str:
    descriptions = []

    for tool in tools:
        descriptions.append(function_schema(tool))
    return "\n".join(json.dumps(schema, ensure_ascii=False) for schema in descriptions)
