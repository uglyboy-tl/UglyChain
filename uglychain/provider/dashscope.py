#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass
from typing import Any, Dict, Optional, Type
from http import HTTPStatus

from loguru import logger
from pydantic import BaseModel

from uglychain.utils import config, retry_decorator
from uglychain.llm import BaseLanguageModel, Instructor


class BadRequestError(Exception):
    pass


class Unauthorized(Exception):
    pass


class RequestLimitError(Exception):
    pass


def not_notry_exception(exception: BaseException):
    if isinstance(exception, BadRequestError):
        return False
    if isinstance(exception, Unauthorized):
        return False
    return True

@dataclass
class DashScope(BaseLanguageModel):
    model: str
    use_max_tokens: bool = True
    MAX_TOKENS: int = 6000
    seed: int = 1234

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
        try:
            response = self.completion_with_backoff(**kwargs)
        except Exception as e:
            if "Range of input length" in str(e) or "Prompt is too long." in str(e):
                if self.model == "qwen-max":
                    kwargs["model"] = "qwen-max-longcontext"
                else:
                    raise e
                logger.warning(
                    f"Model {self.model} does not support {self._num_tokens(self.messages, self.model)} tokens. Trying again with {kwargs['model']}."
                )
                response = self.completion_with_backoff(**kwargs)
            else:
                raise e

        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response.output.choices[0].message.content.strip()

    @retry_decorator(not_notry_exception)
    def completion_with_backoff(self, **kwargs):
        response = self.client.Generation.call(**kwargs)

        status_code, code, message = (
            response.status_code,
            response.code,
            response.message,
        )
        if status_code == HTTPStatus.OK:
            return response
        elif status_code == 400:
            # 400 Bad Request
            raise BadRequestError(f"code: {code}, message:{message}")
        elif status_code == 401:
            # 401 Unauthorized
            raise Unauthorized()
        elif status_code == 429:
            # 404 Not Found
            raise RequestLimitError()
        else:
            raise Exception(
                f"Failed request_id: {response.request_id}, status_code: {status_code}, code: {code}, message:{message}"
            )

    @property
    def _default_params(self) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "seed": self.seed,
            "result_format": "message",
        }
        if self.use_max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        return kwargs

    def _create_client(self):
        try:
            import dashscope
        except ImportError:
            raise ImportError(
                "You need to install `pip install dashscope` to use this provider."
        )
        dashscope.api_key = config.dashscope_api_key
        return dashscope

    def _num_tokens(self, messages: list, model: str):
        if model == "qwen-max" or model == "qwen-max-longcontext":
            logger.trace(
                "qwen-max may change over time. Returning num tokens assuming qwen-turbo."
            )
            return self._num_tokens(messages, model="qwen-turbo")
        try:
            response = self.client.Tokenization.call(model=model, messages=messages)
        except KeyError:
            logger.trace("model not found. Using qwen-turbo encoding.")
            response = self.client.Tokenization.call(
                model="qwen-turbo", messages=messages
            )
        if response.status_code == HTTPStatus.OK:
            return response.usage["input_tokens"]
        else:
            raise Exception(
                f"Failed request_id: {response.request_id}, status_code: {response.status_code}, code: {response.code}, message:{response.message}"
            )

    @property
    def max_tokens(self):
        # add 1000 tokens for answers
        tokens = self._num_tokens(messages=self.messages, model=self.model)
        if not self.MAX_TOKENS > tokens:
            raise Exception(
                f"Prompt is too long. This model's maximum context length is {self.MAX_TOKENS} tokens. your messages required {tokens} tokens"
            )
        if self.model == "qwen-turbo":
            return 1500
        return 2000