"""Base implementation for tools or skills."""
from __future__ import annotations

from abc import ABC
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union
from dataclasses import dataclass

from pydantic import BaseModel


class ToolRunningError(Exception):
    """Raised when a tool fails to run."""


@dataclass
class BaseTool(ABC):
    """Interface AutoChain tools must implement."""

    description: str
    """Used to tell the model how/when/why to use the tool.
    You can provide few-shot examples as a part of the description.
    """

    name: Optional[str] = None
    """The unique name of the tool that clearly communicates its purpose.
    If not provided, it will be named after the func name.
    The more descriptive it is, the easier it would be for model to call the right tool
    """

    arg_description: Optional[Dict[str, Any]] = None
    """Dictionary of arg name and description when using OpenAIFunctionsAgent to provide
    additional argument information"""

    args_schema: Optional[Type[BaseModel]] = None
    """Pydantic model class to validate and parse the tool's input arguments."""

    func: Optional[Callable[..., str]] = None

    def _parse_input(
        self,
        tool_input: Union[str, Dict],
    ) -> Union[str, Dict[str, Any]]:
        """Convert tool input to pydantic model."""
        input_args = self.args_schema
        if isinstance(tool_input, str):
            if input_args is not None:
                key_ = next(iter(input_args.model_fields.keys()))
                input_args.model_validate({key_: tool_input})
            return tool_input
        else:
            if input_args is not None:
                result = input_args.model_validate(tool_input)
                return {k: v for k, v in result.model_dump().items() if k in tool_input}
        return tool_input

    def _to_args_and_kwargs(self, tool_input: Union[str, Dict]) -> Tuple[Tuple, Dict]:
        # For backwards compatibility, if run_input is a string,
        # pass as a positional argument.
        if isinstance(tool_input, str):
            return (tool_input,), {}
        else:
            return (), tool_input

    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        if self.func:
            return self.func(*args, **kwargs)
        else:
            raise NotImplementedError

    def run(
        self,
        tool_input: Union[str, Dict] = "",
        **kwargs: Any,
    ) -> str:
        """Run the tool."""
        try:
            parsed_input = self._parse_input(tool_input)
        except ValueError as e:
            # return exception as tool output
            raise ToolRunningError(f"Tool input args value Error: {e}") from e

        try:
            tool_args, tool_kwargs = self._to_args_and_kwargs(parsed_input)
            tool_output = self._run(*tool_args, **tool_kwargs)
        except (Exception, KeyboardInterrupt) as e:
            raise ToolRunningError(f"Failed to run tool {self.name} due to {e}") from e

        return tool_output
