#!/usr/bin/env python3

import os
from dataclasses import dataclass

from .singleton import singleton


@singleton
@dataclass
class Config:
    # General
    output_format: str = os.getenv("OUTPUT_FORMAT", "yaml")

    # API keys
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    copilot_token: str = os.getenv("COPILOT_TOKEN", "")
    copilot_gpt4_service_url: str = os.getenv("COPILOT_GPT4_SERVICE_URL", "")
    # Yi
    yi_api_key: str = os.getenv("YI_API_KEY", "")
    # Baichuan
    baichuan_api_key: str = os.getenv("BAICHUAN_API_KEY", "")
    # Custom
    custom_token: str = os.getenv("CUSTOM_TOKEN", "")
    custom_url: str = os.getenv("CUSTOM_URL", "")
    custom_model: str = os.getenv("CUSTOM_MODEL", "")
    # Ollama
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    # Dashscope
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    # Zhipuai
    zhipuai_api_key: str = os.getenv("ZHIPUAI_API_KEY", "")
    default_llm: str = os.getenv("DEFAULT_LLM", "YI")
    # SparkAPI
    spark_api_key: str = os.getenv("SPARK_API_KEY", "")
    spark_api_secret: str = os.getenv("SPARK_API_SECRET", "")
    spark_app_id: str = os.getenv("SPARK_APP_ID", "")

    # Embedding Options
    embedding_api_base: str = os.getenv("EMBEDDING_API_BASE", "https://api.openai.com/v1")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", openai_api_key)
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

    # Bing Search
    bing_subscription_key: str = os.getenv("BING_SUBSCRIPTION_KEY", "")
    # Stop Words Dictionary
    stop_words_path: str = os.getenv("STOP_WORDS_PATH", "")


config = Config()
