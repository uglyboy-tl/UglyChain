import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel

from uglychain.llm.tools import tools_schema
from uglychain.utils import config

from .openai_api import ChatGPTAPI


@dataclass
class ChatGPT(ChatGPTAPI):
    api_key: str = config.openai_api_key
    base_url: str = config.openai_api_base
    name: str = "OpenAI"
    use_max_tokens: bool = True
    use_native_tools: bool = field(init=False, default=True)

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> str:
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        if response_model and self.model in [
            "gpt-3.5-turbo-1106",
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-4-0125-preview",
        ]:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = self.completion_with_backoff(**kwargs)
        except Exception as e:
            if "maximum context length" in str(e) and self.name == "OpenAI":
                if self.model != "gpt-4-turbo-preview":
                    kwargs["model"] = "gpt-4-turbo-preview"
                    kwargs["max_tokens"] = 4096
                else:
                    raise e
                logger.warning(
                    f"Model {self.model} does not support {self._num_tokens(self.messages, self.model)+1000} tokens. Trying again with {kwargs['model']}."
                )
                response = self.completion_with_backoff(**kwargs)
            else:
                raise e

        logger.trace(f"kwargs:{kwargs}\nresponse:{response.choices[0].model_dump()}")
        if self.use_native_tools and tools and response.choices[0].message.tool_calls:
            result = response.choices[0].message.tool_calls[0].function
            return json.dumps({"name": result.name, "args": json.loads(result.arguments)})
        return response.choices[0].message.content.strip()

    def get_kwargs(
        self,
        prompt: str,
        response_model: Optional[Type],
        tools: Optional[List[Callable]],
        stop: Union[Optional[str], List[str]],
    ) -> Dict[str, Any]:
        if self.use_native_tools and tools:
            self._generate_validation()
            self._generate_messages(prompt)
            params = self.default_params
            params["tools"] = tools_schema(tools)
            if len(tools) == 1:
                params["tool_choice"] = {"type": "function", "function": {"name": tools[0].__name__}}
            kwargs = {"messages": self.messages, "stop": stop, **params}
            return kwargs
        else:
            return super().get_kwargs(prompt, response_model, tools, stop)

    def _num_tokens(self, messages: list, model: str):
        try:
            import tiktoken
        except ImportError as e:
            raise ImportError("You need to install `pip install tiktoken` to use `use_max_tokens` param.") from e
        if model == "gpt-3.5-turbo-1106":
            # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_message = 4
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif model == "gpt-4-0613":
            tokens_per_message = 3
            tokens_per_name = 1
        elif model.find("gpt-3.5") != -1:
            logger.trace("gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-1106.")
            return self._num_tokens(messages, model="gpt-3.5-turbo-1106")
        elif model.find("gpt-4") != -1:
            logger.trace("gpt-4 may change over time. Returning num tokens assuming gpt-4-0613.")
            return self._num_tokens(messages, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.trace("model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    @property
    def max_tokens(self):
        tokens = self._num_tokens(messages=self.messages, model=self.model) + 1000  # add 1000 tokens for answers
        max_tokens = max(self.MAX_TOKENS - tokens + 1000, 1)
        return 4096 if max_tokens > 4096 else max_tokens
