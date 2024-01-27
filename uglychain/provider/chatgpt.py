from dataclasses import dataclass
from typing import Type, Optional

from loguru import logger
from pydantic import BaseModel

from uglychain.utils import config
from uglychain.llm import Instructor
from .openai_api import ChatGPTAPI


@dataclass
class ChatGPT(ChatGPTAPI):
    api_key: str = config.openai_api_key
    base_url: str = config.openai_api_base
    name: str = "OpenAI"
    use_max_tokens: bool = True

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
        if response_model and self.model in ["gpt-3.5-turbo-1106","gpt-4-1106-preview"]:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = self.completion_with_backoff(**kwargs)
        except Exception as e:
            if "maximum context length" in str(e) and self.name == "OpenAI":
                if self.model == "gpt-3.5-turbo":
                    kwargs["model"] = "gpt-3.5-turbo-16k"
                elif self.model == "gpt-4":
                    kwargs["model"] = "gpt-4-32k"
                else:
                    raise e
                logger.warning(
                    f"Model {self.model} does not support {self._num_tokens(self.messages, self.model)+1000} tokens. Trying again with {kwargs['model']}."
                )
                response = self.completion_with_backoff(**kwargs)
            else:
                raise e

        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response.choices[0].message.content.strip()

    def _num_tokens(self, messages: list, model: str):
        try:
            import tiktoken
        except ImportError:
            raise ImportError(
                "You need to install `pip install tiktoken` to use `use_max_tokens` param."
        )
        if model == "gpt-3.5-turbo" or model == "gpt-3.5-turbo-16k" or model == "gpt-3.5-turbo-1106":
            logger.trace(
                "gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0613."
            )
            return self._num_tokens(messages, model="gpt-3.5-turbo-0613")
        elif model == "gpt-4" or model == "gpt-4-32k" or model == "gpt-4-1106-preview":
            logger.trace(
                "gpt-4 may change over time. Returning num tokens assuming gpt-4-0613."
            )
            return self._num_tokens(messages, model="gpt-4-0613")
        elif model == "gpt-3.5-turbo-0613":
            # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_message = 4
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif model == "gpt-4-0613":
            tokens_per_message = 3
            tokens_per_name = 1
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
        tokens = (
            self._num_tokens(messages=self.messages, model=self.model) + 1000
        )  # add 1000 tokens for answers
        if not self.MAX_TOKENS > tokens:
            raise Exception(
                f"Prompt is too long. This model's maximum context length is {self.MAX_TOKENS} tokens. your messages required {tokens} tokens"
            )
        max_tokens = self.MAX_TOKENS - tokens + 1000
        if self.model == "gpt-4-1106-preview":
            return 4096 if max_tokens > 4096 else max_tokens
        return max_tokens
