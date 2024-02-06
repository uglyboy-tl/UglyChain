#!/usr/bin/env python3

import os
from dataclasses import dataclass
from typing import Optional

from .singleton import singleton


@singleton
@dataclass
class Config:
    # API keys
    # OpenAI
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    copilot_token: Optional[str] = os.getenv("COPILOT_TOKEN")
    copilot_gpt4_service_url: Optional[str] = os.getenv("COPILOT_GPT4_SERVICE_URL")
    # Yi
    yi_api_key: Optional[str] = os.getenv("YI_API_KEY")
    # Baichuan
    baichuan_api_key: Optional[str] = os.getenv("BAICHUAN_API_KEY")
    # Custom
    custom_token: Optional[str] = os.getenv("CUSTOM_TOKEN")
    custom_url: Optional[str] = os.getenv("CUSTOM_URL")
    custom_model: Optional[str] = os.getenv("CUSTOM_MODEL")

    # Gemini
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    # Dashscope
    dashscope_api_key: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    # Zhipuai
    zhipuai_api_key: Optional[str] = os.getenv("ZHIPUAI_API_KEY")
    llm_provider: str = os.getenv("LLM_PROVIDER", "gpt-3.5-turbo")

    # Bing Search
    bing_subscription_key: Optional[str] = os.getenv("BING_SUBSCRIPTION_KEY")
    # Stop Words Dictionary
    stop_words_path: str = os.getenv("STOP_WORDS_PATH", "")


config = Config()
