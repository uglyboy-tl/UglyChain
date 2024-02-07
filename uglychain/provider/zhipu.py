import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel

from uglychain.llm import BaseLanguageModel
from uglychain.utils import config, retry_decorator

from .error import BadRequestError, RequestLimitError, Unauthorized


def not_notry_exception(exception: BaseException):
    if isinstance(exception, BadRequestError):
        return False
    if isinstance(exception, Unauthorized):
        return False
    return True


@dataclass
class ChatGLM(BaseLanguageModel):
    use_max_tokens: bool = False
    MAX_TOKENS: int = 128000
    top_p: float = field(init=False, default=0.7)
    # use_native_tools: bool = field(init=False, default=True)

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
        if self.use_native_tools and response.choices[0].message.tool_calls:
            tool_calls_response = response.choices[0].message.tool_calls[0].function
            if tools:
                return json.dumps({"name": tool_calls_response.name, "args": json.loads(tool_calls_response.arguments)})
            elif response_model:
                return tool_calls_response.arguments
        return response.choices[0].message.content.strip()

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

    @retry_decorator(not_notry_exception)
    def completion_with_backoff(self, **kwargs):
        from zhipuai import APIStatusError

        try:
            return self.client.chat.completions.create(**kwargs)
        except APIStatusError as error:
            status_code = error.status_code
            error_json = json.loads(error.response.text.strip())
            code = error_json.get("error").get("code")
            message = error_json.get("error").get("message")
            if status_code in [400, 404, 435]:
                # 400 Bad Request
                raise BadRequestError(f"code: {code}, message:{message}") from error
            elif status_code == 429 and code in ["1302", "1303", "1305"]:
                # 404 Not Found
                raise RequestLimitError(f"code: {code}, message:{message}") from error
            elif status_code in [401, 429, 434]:
                # 401 Unauthorized
                raise Unauthorized(f"code: {code}, message:{message}") from error
            else:
                raise error
        except Exception as e:
            raise e

    @property
    def max_tokens(self):
        tokens = self._num_tokens(messages=self.messages, model=self.model) + 1000  # add 1000 tokens for answers
        if not self.MAX_TOKENS > tokens:
            raise Exception(
                f"Prompt is too long. This model's maximum context length is {self.MAX_TOKENS} tokens. your messages required {tokens} tokens"
            )
        max_tokens = self.MAX_TOKENS - tokens + 1000
        return 2000 if max_tokens > 2000 else max_tokens
