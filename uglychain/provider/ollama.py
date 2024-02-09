from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel

from uglychain.llm import BaseLanguageModel
from uglychain.utils import config, retry_decorator


@dataclass
class Ollama(BaseLanguageModel):
    top_p: float = 0.9

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> str:
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        response = self.completion_with_backoff(**kwargs)
        logger.trace(f"kwargs:{kwargs}\nresponse:{response['message']}")
        return response["message"]["content"]

    def get_kwargs(
        self,
        prompt: str,
        response_model: Optional[Type[BaseModel]],
        tools: Optional[List[Callable]],
        stop: Union[Optional[str], List[str]],
    ) -> Dict[str, Any]:
        kwargs = super().get_kwargs(prompt, response_model, tools, stop)
        stop_value = kwargs.pop("stop")
        kwargs["options"]["stop"] = stop_value
        if response_model:
            kwargs["format"] = "json"
        return kwargs

    @property
    def default_params(self) -> Dict[str, Any]:
        options = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "seed": self.seed,
        }
        kwargs = {
            "model": self.model,
            "options": options,
        }
        return kwargs

    def _create_client(self):
        try:
            from ollama import Client
        except ImportError as err:
            raise ImportError("You need to install `pip install ollama` to use this provider.") from err
        return Client(host=config.ollama_host)

    @retry_decorator()
    def completion_with_backoff(self, **kwargs):
        return self.client.chat(**kwargs)

    @property
    def max_tokens(self):
        return 2000
