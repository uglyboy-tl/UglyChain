#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass
from typing import Any, Dict, Type, Optional

from loguru import logger
from pydantic import BaseModel

from uglychain.utils import config, retry_decorator
from uglychain.llm import BaseLanguageModel, Instructor

@dataclass
class Gemini(BaseLanguageModel):
    model: str = 'gemini-pro'
    use_max_tokens: bool = False
    is_continuous: bool = True

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
    ) -> str:
        self._generate_validation()
        if self.system_prompt:
            prompt = self.system_prompt + "\n" + prompt
        if response_model:
            instructor = Instructor.from_BaseModel(response_model)
            prompt += "\n" + instructor.get_format_instructions()
        kwargs = {"content": prompt, **self._default_params}
        response = self.completion_with_backoff(**kwargs)

        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response.choices[0].message.content.strip()

    @property
    def _default_params(self) -> Dict[str, Any]:
        kwargs = {}
        return kwargs

    def _create_client(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key, transport='rest')
        except ImportError:
            raise ImportError(
                "You need to install `pip install google-generativeai` to use this provider."
        )
        chat = genai.GenerativeModel(self.model).start_chat(history=[])
        return chat

    @retry_decorator()
    def completion_with_backoff(self, **kwargs):
        return self.client.send_message(**kwargs)

    @property
    def max_tokens(self):
        return 0