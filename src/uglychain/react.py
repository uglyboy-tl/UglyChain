from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, ParamSpec, cast

from rich.live import Live

from .console import Console
from .llm import llm
from .mcp import AppConfig, McpTool, load_tools
from .structured import T
from .tools import function_schema

P = ParamSpec("P")


def react(
    model: str,
    tools: list[Callable] | None = None,
    mcp_config: str = "",
    response_format: type[T] | None = None,
    max_reacts: int = -1,
    console: Console | None = None,
    **api_params: Any,
) -> Callable[[Callable[P, str | list[dict[str, str]] | T]], Callable[P, str | T]]:
    default_model_from_decorator = model
    default_tools: list[Callable] = [] if tools is None else tools
    default_mcp_config = AppConfig.load(mcp_config)
    default_response_format = response_format  # noqa: F841
    default_api_params_from_decorator = api_params.copy()
    default_console = console or Console(show_message=False)

    def parameterized_lm_decorator(
        prompt: Callable[P, str | list[dict[str, str]] | T],
    ) -> Callable[P, str | T]:
        @wraps(prompt)
        def model_call(
            *prompt_args: P.args,
            **prompt_kwargs: P.kwargs,
        ) -> str | T:
            default_console.init()
            default_console.show_result = False
            # Add final answer to the list of tools
            default_tools.insert(0, final_answer)

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

            def react_once(*prompt_args: P.args, acts: list[Action] = None, **prompt_kwargs: P.kwargs):  # type: ignore
                if acts is None:
                    acts = []
                output = prompt(*prompt_args, **prompt_kwargs)
                if isinstance(output, list):
                    output[-1]["content"] += "\n".join(str(a) for a in acts)
                elif isinstance(output, str):
                    return output + "\n".join(str(a) for a in acts)

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                future = executor.submit(loop.run_until_complete, load_tools(default_mcp_config))
                mcp_clients, mcp_tools = future.result()

                tool_names = [f"`{tool.__name__}`" for tool in default_tools]
                tool_names.extend(f"`{tool.name}`" for tool in mcp_tools)
                react_once.__doc__ = (prompt.__doc__ if prompt.__doc__ else "") + SYSTEM_PROMPT.format(
                    tool_names=", ".join(tool_names),
                    tool_descriptions=_tool_descriptions(default_tools) + "\n" + _mcp_tool_descriptions(mcp_tools),
                )

                llm_tool_call: Callable = llm(
                    default_model_from_decorator,
                    console=default_console,
                    stop=["Observation:"],
                    **default_api_params_from_decorator,
                )(react_once)

                def _call_tool(name: str, args: dict[str, Any]) -> str:
                    for tool in default_tools:
                        if tool.__name__ == name:
                            return tool(**args)
                    for tool in mcp_tools:
                        if tool.name == name:
                            future = executor.submit(loop.run_until_complete, tool._arun(**args))
                            return future.result()
                    raise ValueError(f"Can't find tool {name}")

                react_times = 0
                result = llm_tool_call(*prompt_args, **prompt_kwargs)
                assert isinstance(result, str)
                default_console.off()
                with Live(default_console.react_table, console=default_console.console) as live:
                    act = Action.from_response(result, _call_tool)
                    default_console.log_react(act.__dict__, live)
                    acts = [act]
                    while not act.done and (max_reacts == -1 or react_times < max_reacts):
                        result = cast(str, llm_tool_call(*prompt_args, acts=acts, **prompt_kwargs))
                        act = Action.from_response(result, _call_tool)
                        default_console.log_react(act.__dict__, live)
                        react_times += 1
                        acts.append(act)
                # Close all clients
                for client in mcp_clients:
                    executor.submit(loop.run_until_complete, client.close())
            loop.close()
            response: str | T = act.obs
            if not act.done and react_times >= max_reacts or default_response_format is not None:
                response = llm_final_call(*prompt_args, acts=acts, **prompt_kwargs)  # type: ignore
            assert not isinstance(response, list)
            return response

        model_call.__api_params__ = default_api_params_from_decorator  # type: ignore
        model_call.__func__ = prompt  # type: ignore

        return model_call  # type: ignore

    return parameterized_lm_decorator  # type: ignore[return-value]


SYSTEM_PROMPT = """You are an expert assistant who can solve any task using tools. You will be given a task to solve as best you can.
To do so, you have been given access to a list of tools: [{tool_names}].
To solve the task, you must plan forward to proceed in a series of steps, in a cycle of 'Thought:', 'Action:', 'Action Input:', and 'Observation:' sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning towards solving the task and the tools that you want to use.
Then in the 'Action:' and 'Action Input:' sequence, you should tell system what tool to use and what arguments to use.
The action result will then appear in the 'Observation:' field, which will be available as input for the next step. And you do not need to generate this part, it will be automatically filled by the system.
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
"""


def final_answer(answer: str) -> str:
    """When get Final Answer, use this tool to return the answer and finishes the task."""
    return answer


@dataclass
class Action:
    thought: str
    tool: str
    args: dict
    obs: str

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
    def from_response(cls, text: str, call: Callable[[str, dict[str, Any]], str]) -> Action:
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
        tool = func_name
        args = json.loads(func_args.replace("'", '"'))
        return cls(
            thought=text,
            tool=tool,
            args=args,
            obs=call(tool, args),  # type: ignore
        )


def _tool_descriptions(tools: list[Callable]) -> str:
    descriptions = []

    for tool in tools:
        schema = function_schema(tool)
        markdown = f"### {schema['name']}\n"
        markdown += f"{json.dumps(schema, ensure_ascii=False)}\n"
        descriptions.append(markdown)
    return "\n".join(descriptions)


def _mcp_tool_descriptions(mcp_tools: list[McpTool]) -> str:
    descriptions = []

    for tool in mcp_tools:
        schema = tool.args_schema
        schema.update({"name": tool.name})
        markdown = f"### {tool.name}\n"
        markdown += f"{json.dumps(schema, ensure_ascii=False)}\n"
        descriptions.append(markdown)
    return "\n".join(descriptions)
