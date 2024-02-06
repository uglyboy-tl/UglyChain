#!/usr/bin/env python3

from uglychain.llm import BaseLanguageModel
from uglychain.utils import config

from .baichuan import Baichuan
from .chatgpt import ChatGPT
from .copilot import Copilot
from .custom import Custom
from .dashscope import DashScope
from .gemini import Gemini
from .yi import Yi
from .zhipu import ChatGLM

LLM_PROVIDERS = {
    "gpt-3.5-turbo": (ChatGPT, {"model": "gpt-3.5-turbo-0125", "MAX_TOKENS": 16384}),
    "gpt-4": (ChatGPT, {"model": "gpt-4", "MAX_TOKENS": 8192}),
    "gpt-4-turbo": (ChatGPT, {"model": "gpt-4-turbo-preview", "MAX_TOKENS": 128000}),
    "copilot-3.5": (Copilot, {"model": "gpt-3.5-turbo"}),
    "copilot-4": (Copilot, {"model": "gpt-4"}),
    "yi": (Yi, {"model": "yi-34b-chat-v08"}),
    "yi-32k": (Yi, {"model": "yi-34b-chat-32k-v01"}),
    "baichuan-turbo": (Baichuan, {"model": "Baichuan2-Turbo"}),
    "baichuan-turbo-192k": (Baichuan, {"model": "Baichuan2-Turbo-192k"}),
    "baichuan-pro": (Baichuan, {"model": "Baichuan2-53B"}),
    "custom": (Custom, {}),
    "gemini": (Gemini, {"model": "gemini-pro"}),
    "qwen": (DashScope, {"model": "qwen-max", "MAX_TOKENS": 6000}),
    "qwen-turbo": (DashScope, {"model": "qwen-turbo", "MAX_TOKENS": 6000}),
    "qwen-plus": (DashScope, {"model": "qwen-plus", "MAX_TOKENS": 30000}),
    "qwen-28k": (DashScope, {"model": "qwen-max-longcontext", "MAX_TOKENS": 28000}),
    "glm-4": (ChatGLM, {"model": "glm-4", "MAX_TOKENS": 128000}),
    "glm-3": (ChatGLM, {"model": "glm-3-turbo", "MAX_TOKENS": 128000}),
}


def get_llm_provider(llm_provider_name: str = config.llm_provider, is_init_delay: bool = False) -> BaseLanguageModel:
    """
    Get the LLM provider.

    Args:
        llm_provider_name: The name of the LLM provider.

    Returns:
        The LLMProvider object.
    """

    if llm_provider_name in LLM_PROVIDERS.keys():
        provider, kwargs = LLM_PROVIDERS[llm_provider_name]
        kwargs["is_init_delay"] = is_init_delay
        return provider(**kwargs)
    else:
        raise NotImplementedError(f"{llm_provider_name} LLM provider not implemented")


__all__ = ["get_llm_provider"]
