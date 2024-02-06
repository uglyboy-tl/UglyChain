#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel

from uglychain.llm import BaseLanguageModel
from uglychain.utils import config, retry_decorator


@dataclass
class Gemini(BaseLanguageModel):
    model: str
    use_max_tokens: bool = False

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> str:
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        response = self.completion_with_backoff(**kwargs)
        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response.choices[0].message.content.strip()

    # TODO: Set stop to stop_sequences in params
    def get_kwargs(
        self,
        prompt: str,
        response_model: Optional[Type],
        tools: Optional[List[Callable]],
        stop: Union[Optional[str], List[str]] = None,
    ) -> Dict[str, Any]:
        kwargs = super().get_kwargs(prompt, response_model, tools, stop)
        contents = kwargs["messages"]
        kwargs.pop("messages")
        kwargs["contents"] = contents
        return kwargs

    def _generate_messages(self, prompt: str) -> List[Dict[str, str]]:
        """Generate the list of messages for the conversation.

        Args:
            prompt (str): The user prompt.

        Returns:
            List[Dict[str, str]]: The list of messages.

        """
        if not self.is_continuous:
            self.messages = []
            if hasattr(self, "system_prompt") and self.system_prompt:
                self.messages.append({"role": "system", "parts": [self.system_prompt]})
        if prompt:
            self.messages.append({"role": "user", "parts": [prompt]})
        return self.messages

    @property
    def default_params(self) -> Dict[str, Any]:
        config = self.client.types.GenerationConfig(max_output_tokens=self.max_tokens, temperature=self.temperature)
        kwargs = {
            "generation_config": config,
        }
        return kwargs

    def _create_client(self):
        try:
            import google.generativeai as genai

            genai.configure(api_key=config.gemini_api_key, transport="rest")
        except ImportError as e:
            raise ImportError("You need to install `pip install google-generativeai` to use this provider.") from e
        return genai

    @retry_decorator()
    def completion_with_backoff(self, **kwargs):
        model = self.client.GenerativeModel(self.model)
        return model.generate_content(**kwargs)

    @property
    def max_tokens(self):
        return 2000
