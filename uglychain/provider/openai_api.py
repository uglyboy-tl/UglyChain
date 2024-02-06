#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Callable, List, Optional, Type, Union

import openai
from loguru import logger
from pydantic import BaseModel
from requests.exceptions import SSLError

from uglychain.llm import BaseLanguageModel
from uglychain.utils import retry_decorator


def not_notry_exception(exception: BaseException) -> bool:
    if isinstance(exception, openai.BadRequestError):
        return False
    elif isinstance(exception, openai.AuthenticationError):
        return False
    elif isinstance(exception, openai.PermissionDeniedError):
        return False
    elif (
        isinstance(exception, openai.APIConnectionError)
        and exception.__cause__ is not None
        and isinstance(exception.__cause__, SSLError)
    ):
        return False
    else:
        return True


@dataclass
class ChatGPTAPI(BaseLanguageModel):
    api_key: str
    base_url: str
    name: str
    MAX_TOKENS: int = 4096

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> str:
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        response = self.completion_with_backoff(**kwargs)
        logger.trace(f"kwargs:{kwargs}\nresponse:{response.choices[0].model_dump()}")
        return response.choices[0].message.content.strip()

    @retry_decorator(not_notry_exception)
    def completion_with_backoff(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

    def _create_client(self):
        return openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

    @property
    def max_tokens(self):
        tokens = self._num_tokens(messages=self.messages, model=self.model) + 1000  # add 1000 tokens for answers
        if not self.MAX_TOKENS > tokens:
            raise Exception(
                f"Prompt is too long. This model's maximum context length is {self.MAX_TOKENS} tokens. your messages required {tokens} tokens"
            )
        max_tokens = self.MAX_TOKENS - tokens + 1000
        return max_tokens
