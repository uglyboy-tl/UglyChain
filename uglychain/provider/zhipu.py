#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass
from typing import Any, Dict, Type, Optional

from loguru import logger
from pydantic import BaseModel

from uglychain.utils import config, retry_decorator
from uglychain.llm import BaseLanguageModel, Instructor

@dataclass
class ChatGLM(BaseLanguageModel):
    model: str
    use_max_tokens: bool = False
    MAX_TOKENS: int = 128000

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
    ) -> str:
        self._generate_validation()
        if response_model:
            instructor = Instructor.from_BaseModel(response_model)
            prompt += "\n" + instructor.get_format_instructions()
        self._generate_messages(prompt)
        kwargs = {"messages": self.messages, **self._default_params}
        response = self.completion_with_backoff(**kwargs)

        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response.choices[0].message.content.strip()

    @property
    def _default_params(self) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "do_sample": True,
            "temperature": self.temperature,
        }
        if self.use_max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        return kwargs

    def _create_client(self):
        try:
            from zhipuai import ZhipuAI
        except ImportError:
            raise ImportError(
                "You need to install `pip install dashscope` to use this provider."
        )
        return ZhipuAI(api_key=config.zhipuai_api_key)

    @retry_decorator()
    def completion_with_backoff(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

    @property
    def max_tokens(self):
        tokens = self._num_tokens(messages=self.messages, model=self.model) + 1000 # add 1000 tokens for answers
        if not self.MAX_TOKENS > tokens:
            raise Exception(f"Prompt is too long. This model's maximum context length is {self.MAX_TOKENS} tokens. your messages required {tokens} tokens")
        max_tokens = self.MAX_TOKENS - tokens + 1000
        return 2000 if max_tokens > 2000 else max_tokens
