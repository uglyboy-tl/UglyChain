from __future__ import annotations

import ast
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, overload

from .config import config
from .console import Console
from .default_tools import final_answer
from .llm import gen_prompt, llm
from .schema import Messages, P, T
from .tool import MCP, Tool
from .utils import retry


@overload
def react(
    model: str = "",
    tools: list[Tool | MCP] | None = None,
    *,
    response_format: None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str]]: ...


@overload
def react(
    model: str = "",
    tools: list[Tool | MCP] | None = None,
    *,
    response_format: type[T],
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, T]]: ...


def react(
    model: str = "",
    tools: list[Tool | MCP] | None = None,
    *,
    response_format: type[T] | None = None,
    max_steps: int = -1,
    console: Console | None = None,
    need_final_answer: bool = False,
    **api_params: Any,
) -> Callable[[Callable[P, str | Messages | None]], Callable[P, str | T]]:
    default_model_from_decorator = model if model else config.default_model
    default_tools: list[Tool] = [final_answer]
    if tools:
        for tool in tools:
            if isinstance(tool, MCP):
                default_tools.extend(tool.tools)
            else:
                default_tools.append(tool)
    default_response_format = response_format  # noqa: F841
    default_api_params_from_decorator = api_params.copy()
    default_console = console or Console(show_message=False, show_react=True)

    def parameterized_lm_decorator(
        prompt: Callable[P, str | Messages | None],
    ) -> Callable[P, str | T]:
        @wraps(prompt)
        def model_call(
            *prompt_args: P.args,
            **prompt_kwargs: P.kwargs,
        ) -> str | T:
            default_console.init()
            react_console = Console(
                False,
                False,
                False,
                False,
                False if default_console.show_react else default_console.show_message,
                default_console.show_react,
            )
            tool_names = [f"`{tool.name}`" for tool in default_tools]

            def react_once(*prompt_args: P.args, acts: list[Action], **prompt_kwargs: P.kwargs):  # type: ignore
                output = gen_prompt(prompt, *prompt_args, **prompt_kwargs)
                if isinstance(output, list):
                    if acts:
                        output.append({"role": "assistant", "content": str(acts[-1])})
                    return output
                elif isinstance(output, str):
                    return output + "\n".join(str(a) for a in acts)
                else:
                    raise ValueError("Invalid output type")

            react_once.__doc__ = SYSTEM_PROMPT.format(
                tool_names=", ".join(tool_names),
                tool_descriptions=_tool_descriptions(default_tools),
            )

            @retry(n=config.llm_max_retry, timeout=config.llm_timeout, wait=config.llm_wait_time)
            def react_response_action_with_retry(*args: Any, **kwargs: Any) -> Action:
                result = llm(
                    model=default_model_from_decorator,
                    console=react_console,
                    map_keys=None,
                    response_format=None,
                    n=None,
                    tools=None,
                    stop=["Observation:"],
                    **default_api_params_from_decorator,
                )(react_once)(*args, **kwargs)
                act = Action.from_response(result, default_console)
                return act

            def final_call(*prompt_args: P.args, acts: list[Action], **prompt_kwargs: P.kwargs):  # type: ignore
                output = gen_prompt(prompt, *prompt_args, **prompt_kwargs)
                history = "\n".join(str(a) for a in acts)
                if isinstance(output, list):
                    output.append(
                        {"role": "assistant", "content": str(acts[-1]) + "\n-----\n Now you must give an final answer!"}
                    )
                    return output
                elif isinstance(output, str):
                    return output + f"\n-----{history}\n-----\n Now you must give an final answer!"
                else:
                    raise ValueError("Invalid output type")

            final_call.__doc__ = prompt.__doc__ if prompt.__doc__ else ""

            llm_final_call = llm(
                default_model_from_decorator,
                response_format=default_response_format,
                console=react_console,
                map_keys=None,
                need_retry=True,
                n=None,
                tools=None,
                **default_api_params_from_decorator,
            )(final_call)

            default_console.log_model_usage_pre(default_model_from_decorator, prompt, prompt_args, prompt_kwargs)

            react_times = 0
            acts: list[Action] = []
            act = Action()
            while react_times == 0 or not act.done and (max_steps == -1 or react_times < max_steps):
                react_times += 1
                default_console.rule(f"Step {react_times}", default_console.show_react, align="left")
                act = react_response_action_with_retry(*prompt_args, acts=acts, **prompt_kwargs)
                acts.append(act)

            response: str | T = act.obs
            if not act.done and react_times >= max_steps or default_response_format is not None or need_final_answer:
                response = llm_final_call(*prompt_args, acts=acts, **prompt_kwargs)
            default_console.stop()
            return response

        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        return model_call

    return parameterized_lm_decorator


SYSTEM_PROMPT = """You are an expert assistant who can solve any task using tools. You will be given a task to solve as best you can.
To do so, you have been given access to the following tools: [{tool_names}].

To solve the task, you must plan forward to proceed in a series of steps, in a cycle of 'Thought:', 'Action:', 'Action Input:', and 'Observation:' sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning towards solving the task and the tools that you want to use.
Then in the 'Action:' and 'Action Input:' sequence, you should tell system what tool to use and what arguments to use.
The action result will then appear in the 'Observation:' field, which will be available as input for the next step. And you do not need to generate this part, it will be automatically filled by the system. The observation will always be a string: it can represent a file, like "image_1.jpg".
In the end you have to return a final answer using the `final_answer` tool.

## Example
An fake example:
```
Task:
the input question you must answer

Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action with JSON format representing the kwargs (e.g. {{"text": "hello world", "num_beams": 5}})
Observation: the result of the action

... (this Thought/Action/Action Input/Observation can be repeated zero or more times)

Thought: I now know the final answer
Action: final_answer
Action Input: {{"answer":"<answer>"}}
```

## Tools
{tool_descriptions}

## Instructions
1. ALWAYS provide a tool call, else you will fail.
2. Always use the right arguments for the tools. Never use variable names as the action arguments, use the value instead.
3. Call a tool only when needed: do not call the search agent if you do not need information, try to solve the task yourself. If no tool call is needed, use final_answer tool to return your answer.
4. Never re-do a tool call that you previously did with the exact same parameters.
"""


@dataclass
class Action:
    thought: str = ""
    tool: str = ""
    args: dict = field(default_factory=dict)
    obs: str = ""

    @property
    def done(self) -> bool:
        if self.tool == "final_answer":
            return True
        else:
            return False

    def __repr__(self) -> str:
        return self.info

    @property
    def info(self) -> str:
        if self.done:
            return f"\nThought: {self.thought}\nAction: Finish\nObservation: {self.obs}"
        return f"\nThought: {self.thought}\nAction: {self.tool}\nAction Input: {self.args}\nObservation: {self.obs}"

    @classmethod
    def from_response(cls, text: str, console: Console) -> Action:
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
            func_name = text[i + len(special_func_token) : j].strip().split("#")[0]
            func_args = text[j + len(special_args_token) : k].strip().split("#")[0]
            match = re.search(r"(\{.*\})", func_args, re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if match:
                func_args = match.group()
            else:
                raise ValueError("Can't parse the Action Input")
            text = text[:i].strip()  # Return the response before tool call, i.e., `Thought`
            if text.startswith("Thought:"):
                text = text[len("Thought:") :]
        # return (func_name is not None), func_name, func_args, text
        if func_name is None or func_args is None:
            raise ValueError("Can't parse the response")
        console.log(text, console.show_react, style="yellow")
        tool = func_name
        args = ast.literal_eval(func_args)
        try:
            obs = Tool.call_tool(tool, console, **args)
            console.log(obs, console.show_react, style="bold green")
        except Exception as e:
            obs = f"Error: {e}"
            console.log(obs, console.show_react, style="bold red")
        return cls(
            thought=text,
            tool=tool,
            args=args,
            obs=obs,
        )


def _tool_descriptions(tools: list[Tool]) -> str:
    descriptions = []

    for tool in tools:
        markdown = f"### {tool.name}\n"
        markdown += f"> {tool.description}\n\n"
        markdown += f"{json.dumps(tool.args_schema, ensure_ascii=False)}\n"
        descriptions.append(markdown)
    return "\n".join(descriptions)
