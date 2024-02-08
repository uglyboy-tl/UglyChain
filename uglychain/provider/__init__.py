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
    Model.GPT3_TURBO: (ChatGPT, {"MAX_TOKENS": 16384}),
    Model.GPT4: (ChatGPT, {"MAX_TOKENS": 8192}),
    Model.GPT4_TURBO: (ChatGPT, {"MAX_TOKENS": 128000}),
    Model.COPILOT3_TURBO: (Copilot, {"model": "gpt-3.5-turbo"}),
    Model.COPILOT4: (Copilot, {"model": "gpt-4"}),
    Model.YI: (Yi, {"MAX_TOKENS": 4096}),
    Model.YI_FUNCTION: (Yi, {"MAX_TOKENS": 16384}),
    Model.YI_LONGCONTEXT: (Yi, {"MAX_TOKENS": 32768}),
    Model.BAICHUAN_TURBO: (Baichuan, {}),
    Model.BAICHUAN_TURBO_192K: (Baichuan, {}),
    Model.BAICHUAN_PRO: (Baichuan, {}),
    Model.CUSTOM: (Custom, {"model": config.custom_model}),
    Model.GEMINI: (Gemini, {}),
    Model.QWEN: (DashScope, {"MAX_TOKENS": 6000}),
    Model.QWEN_TURBO: (DashScope, {"MAX_TOKENS": 6000}),
    Model.QWEN_PLUS: (DashScope, {"MAX_TOKENS": 30000}),
    Model.QWEN_LONGCONTEXT: (DashScope, {"MAX_TOKENS": 28000}),
    Model.GLM4: (ChatGLM, {"MAX_TOKENS": 128000}),
    Model.GLM3: (ChatGLM, {"MAX_TOKENS": 128000}),
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
        if kwargs.get("model") is None:
            kwargs["model"] = llm_provider.value
        return provider(**kwargs)
    else:
        raise NotImplementedError(f"{llm_provider} LLM provider not implemented")


__all__ = ["get_llm_provider", "Model"]
