import json
from dataclasses import dataclass
from typing import Callable, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel

from uglychain.utils import config

from .openai_api import ChatGPTAPI


@dataclass
class Yi(ChatGPTAPI):
    api_key: str = config.yi_api_key
    base_url: str = "https://api.01ww.xyz/v1"
    name: str = "Yi"
    use_max_tokens: bool = False

    def __post_init__(self):
        super().__post_init__()
        if self.model in ["yi-34b-chat-creation-v01"]:
            self.use_native_tools = True

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> str:
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        if "tools" in kwargs:
            functions = kwargs.pop("tools")
            new_functions = []
            for function in functions:
                function["function"]["parameters"]["$schema"] = "http://json-schema.org/draft-04/schema#"
                function["function"]["parameters"]["additionalProperties"] = False
                function["function"]["parameters"]["title"] = function["function"]["name"]
                new_functions.append(function.get("function"))
            kwargs["functions"] = new_functions
        if "tool_choice" in kwargs:
            kwargs["function_call"] = kwargs.pop("tool_choice")["function"]
        response = self.completion_with_backoff(**kwargs)
        logger.trace(f"kwargs:{kwargs}\nresponse:{response.choices[0].model_dump()}")
        if self.use_native_tools and response.choices[0].message.tool_calls:
            tool_calls_response = response.choices[0].message.tool_calls[0].function
            if tools:
                return json.dumps({"name": tool_calls_response.name, "args": json.loads(tool_calls_response.arguments)})
            elif response_model:
                return tool_calls_response.arguments
        return response.choices[0].message.content.strip()
