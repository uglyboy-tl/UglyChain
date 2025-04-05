from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from .utils import parse_to_dict


@dataclass
class Action:
    thought: str = ""
    tool: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    obs: str = field(init=False, default="")
    image: str | None = field(init=False, default=None)

    def _format_args(self) -> str:
        return "".join([f"<{k}>{v}</{k}>" for k, v in self.args.items()])

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
    def from_response(cls, text: str) -> Action:
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
            return cls(
                thought=text,
                tool=_fix_func_name(func_name),
                args=func_args,
            )
        raise ValueError("Can't parse the response, No `Action` or `Action Input`")


def _fix_func_name(func_name: str) -> str:
    name = func_name.strip()

    # 如果函数名是 ```name``` 或 `name` 形式
    pattern = r"(`{1,3})(.*?)(\1)"
    search = re.search(pattern, name)
    if search:
        name = search.group(2)
    return name
