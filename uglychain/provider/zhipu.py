import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel

from uglychain.llm import BaseLanguageModel
from uglychain.llm.tools import tools_schema
from uglychain.utils import config, retry_decorator


@dataclass
class ChatGLM(BaseLanguageModel):
    model: str
    use_max_tokens: bool = False
    MAX_TOKENS: int = 128000
    top_p: float = field(init=False, default=0.7)

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> str:
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        if stop:
            if isinstance(stop, str):
                kwargs["stop"] = [stop]
            elif isinstance(stop, list):
                kwargs["stop"] = stop[0:1]
        else:
            kwargs.pop("stop")
        response = self.completion_with_backoff(**kwargs)
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

    @property
    def default_params(self) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "do_sample": True,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        if self.use_max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        return kwargs

    def _create_client(self):
        try:
            from zhipuai import ZhipuAI
        except ImportError as err:
            raise ImportError("You need to install `pip install dashscope` to use this provider.") from err
        return ZhipuAI(api_key=config.zhipuai_api_key)

    @retry_decorator()
    def completion_with_backoff(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

    @property
    def max_tokens(self):
        tokens = self._num_tokens(messages=self.messages, model=self.model) + 1000  # add 1000 tokens for answers
        if not self.MAX_TOKENS > tokens:
            raise Exception(
                f"Prompt is too long. This model's maximum context length is {self.MAX_TOKENS} tokens. your messages required {tokens} tokens"
            )
        max_tokens = self.MAX_TOKENS - tokens + 1000
        return 2000 if max_tokens > 2000 else max_tokens
