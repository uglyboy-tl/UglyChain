#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel

from uglychain.llm.base import BaseLanguageModel


@dataclass
class AISuite(BaseLanguageModel):
    name: str = "AISuite"
    use_max_tokens: bool = False
    top_p: float = field(init=False, default=0.7)

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> Any:
        """Ask a question and return the user's response.

        Args:
            prompt (str, optional): The question prompt.
            response_model (BaseModel, optional): The response model.

        Returns:
            str: The user's response.

        """
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        response = self.completion_with_backoff(**kwargs)
        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response.choices[0].message.content.strip()

    def completion_with_backoff(self, **kwargs):
        model = kwargs.pop("model")
        messages = kwargs.pop("messages")
        return self.client.chat.completions.create(model=model, messages=messages, **kwargs)

    def _create_client(self):
        try:
            import aisuite as ai
        except ImportError as err:
            raise ImportError("You need to install `pip install aisuite` to use this provider.") from err
        return ai.Client()

    @property
    def max_tokens(self):
        pass
