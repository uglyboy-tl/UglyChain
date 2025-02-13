from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from .console import Console
from .tool import Tool
from .utils import parse_to_dict


@dataclass
class Action:
    thought: str = ""
    tool: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    console: Console = field(default_factory=Console)
    image: str | None = field(init=False, default=None)

    def _call_tool_with_logging(self) -> str:
        try:
            result = Tool.call_tool(self.tool, self.console, **self.args)
            if "\u0001image:" in result:
                result, self.image = result.split("\u0001image:")  # 使用 "\u0001" + "image:" 作为分隔符，分割结果和图片
            self.console.log(_short_result(result), self.console.show_react, style="bold green")
            return result
        except Exception as e:
            error_message = f"Error: {e}"
            self.console.log(error_message, self.console.show_react, style="bold red")
            return error_message

    def _format_args(self) -> str:
        return "".join([f"<{k}>{v}</{k}>" for k, v in self.args.items()])

    @cached_property
    def obs(self) -> str:
        return self._call_tool_with_logging()

    @cached_property
    def done(self) -> bool:
        return self.tool == "final_answer"

    def __repr__(self) -> str:
        return self.info

    @cached_property
    def info(self) -> str:
        return (
            f"\nThought: {self.thought}\nAction: Finish\nObservation: {self.obs}"
            if self.done
            else f"\nThought: {self.thought}\nAction: {self.tool}\nAction Input: {self._format_args()}\nObservation: {self.obs}"
        )

    @classmethod
    def from_response(cls, text: str, console: Console) -> Action:
        special_func_token = "\nAction:"
        special_args_token = "\nAction Input:"
        special_obs_token = "\nObservation:"
        i, j, k = text.rfind(special_func_token), text.rfind(special_args_token), text.rfind(special_obs_token)
        if 0 <= i < j:
            if k < j:
                text = text.rstrip() + special_obs_token
            k = text.rfind(special_obs_token)
            func_name = text[i + len(special_func_token) : j].strip().split("#")[0]
            func_args = parse_to_dict(text[j + len(special_args_token) : k])
            text = text[:i].strip()
            if text.startswith("Thought:"):
                text = text[len("Thought:") :]
            console.log(text, console.show_react, style="yellow")
            return cls(
                thought=text,
                tool=_fix_func_name(func_name),
                args=func_args,
                console=console,
            )
        raise ValueError("Can't parse the response, No `Action` or `Action Input`")


def _fix_func_name(func_name: str) -> str:
    name = func_name.strip()

    # 如果函数名是 ```name``` 或 `name` 形式
    pattern = r"(`{1,3})(.*?)(\1)"
    search = re.search(pattern, name)
    if search:
        name = search.group(2)
        print(f"fix {func_name} to {name}")
    return name


def _short_result(result: str) -> str:
    lines = result.split("\n")
    if len(lines) > 10:
        return "\n".join(lines[:10]) + "\n..."
    elif len(result) > 200:
        return result[:200] + "..."
    else:
        return result
