#!/usr/bin/env python3

from uglychain.llm import BaseLanguageModel
from uglychain.utils import config

from .baichuan import Baichuan
from .chatgpt import ChatGPT
from .copilot import Copilot
from .custom import Custom
from .dashscope import DashScope
from .gemini import Gemini
from .model import Model
from .ollama import Ollama
from .yi import Yi
from .zhipu import ChatGLM

LLM_PROVIDERS = {
    Model.GPT3_TURBO: (ChatGPT, {"model": "gpt-3.5-turbo-0125", "MAX_TOKENS": 16384}),
    Model.GPT4: (ChatGPT, {"model": "gpt-4", "MAX_TOKENS": 8192}),
    Model.GPT4_TURBO: (ChatGPT, {"model": "gpt-4-turbo-preview", "MAX_TOKENS": 128000}),
    Model.COPILOT3_TURBO: (Copilot, {"model": "gpt-3.5-turbo"}),
    Model.COPILOT4: (Copilot, {"model": "gpt-4"}),
    Model.YI: (Yi, {"model": "yi-34b-chat-v08"}),
    Model.YI_32K: (Yi, {"model": "yi-34b-chat-32k-v01"}),
    Model.BAICHUAN_TURBO: (Baichuan, {"model": "Baichuan2-Turbo"}),
    Model.BAICHUAN_TURBO_192K: (Baichuan, {"model": "Baichuan2-Turbo-192k"}),
    Model.BAICHUAN_PRO: (Baichuan, {"model": "Baichuan2-53B"}),
    Model.CUSTOM: (Custom, {"model": config.custom_model}),
    Model.GEMINI: (Gemini, {"model": "gemini-pro"}),
    Model.QWEN: (DashScope, {"model": "qwen-max", "MAX_TOKENS": 6000}),
    Model.QWEN_TURBO: (DashScope, {"model": "qwen-turbo", "MAX_TOKENS": 6000}),
    Model.QWEN_PLUS: (DashScope, {"model": "qwen-plus", "MAX_TOKENS": 30000}),
    Model.QWEN_28K: (DashScope, {"model": "qwen-max-longcontext", "MAX_TOKENS": 28000}),
    Model.GLM4: (ChatGLM, {"model": "glm-4", "MAX_TOKENS": 128000}),
    Model.GLM3: (ChatGLM, {"model": "glm-3-turbo", "MAX_TOKENS": 128000}),
    Model.OLLAMA: (Ollama, {"model": config.ollama_model}),
}

DEFAULT_MODEL = getattr(Model, config.default_llm, Model.GPT3_TURBO)


def get_llm_provider(llm_provider: Model, is_init_delay: bool = False) -> BaseLanguageModel:
    """
    Get the LLM provider.

    Args:
        llm_provider_name: The name of the LLM provider.

    Returns:
        The LLMProvider object.
    """
    if llm_provider == Model.DEFAULT:
        llm_provider = DEFAULT_MODEL
    if llm_provider in LLM_PROVIDERS.keys():
        provider, kwargs = LLM_PROVIDERS[llm_provider]
        kwargs["is_init_delay"] = is_init_delay
        return provider(**kwargs)
    else:
        raise NotImplementedError(f"{llm_provider} LLM provider not implemented")


__all__ = ["get_llm_provider", "Model"]
