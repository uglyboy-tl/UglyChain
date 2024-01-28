#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass
from typing import Any, Dict, List, Type, Optional

from loguru import logger
from pydantic import BaseModel

from uglychain.utils import config, retry_decorator
from uglychain.llm import BaseLanguageModel, Instructor


@dataclass
class Gemini(BaseLanguageModel):
    model: str
    use_max_tokens: bool = False

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
        kwargs = {"content": self.messages, **self._default_params}
        response = self.completion_with_backoff(**kwargs)

        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response.choices[0].message.content.strip()

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
    def _default_params(self) -> Dict[str, Any]:
        config = self.client.types.GenerationConfig(
            max_output_tokens=self.max_tokens, temperature=self.temperature
        )
        kwargs = {
            "generation_config": config,
        }
        return kwargs

    def _create_client(self):
        try:
            import google.generativeai as genai

            genai.configure(api_key=config.gemini_api_key, transport="rest")
        except ImportError:
            raise ImportError(
                "You need to install `pip install google-generativeai` to use this provider."
            )
        return genai

    @retry_decorator()
    def completion_with_backoff(self, **kwargs):
        model = self.client.GenerativeModel(self.model)
        return model.generate_content(**kwargs)

    @property
    def max_tokens(self):
        return 2000
