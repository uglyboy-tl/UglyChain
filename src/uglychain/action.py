from __future__ import annotations

from dataclasses import dataclass, field

from .console import Console
from .tool import Tool
from .utils import parse_to_dict


@dataclass
class Action:
    thought: str = ""
    tool: str = ""
    args: dict = field(default_factory=dict)
    console: Console = field(default_factory=Console)

    @property
    def obs(self) -> str:
        if not hasattr(self, "_obs"):
            try:
                self._obs = Tool.call_tool(self.tool, self.console, **self.args)
                self.console.log(self._obs, self.console.show_react, style="bold green")
            except Exception as e:
                self._obs = f"Error: {e}"
                self.console.log(self._obs, self.console.show_react, style="bold red")
        return self._obs

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
        xml_args = "".join([f"<{k}>{v}</{k}>" for k, v in self.args.items()])
        return f"\nThought: {self.thought}\nAction: {self.tool}\nAction Input: {xml_args}\nObservation: {self.obs}"

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
            func_args = parse_to_dict(text[j + len(special_args_token) : k])
            text = text[:i].strip()  # Return the response before tool call, i.e., `Thought`
            if text.startswith("Thought:"):
                text = text[len("Thought:") :]
        if func_name is None or func_args is None:
            raise ValueError("Can't parse the response, No `Action` or `Action Input`")
        console.log(text, console.show_react, style="yellow")
        return cls(
            thought=text,
            tool=func_name,
            args=func_args,
            console=console,
        )
