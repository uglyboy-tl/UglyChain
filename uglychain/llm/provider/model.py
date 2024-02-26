#!/usr/bin/env python3
from uglychain.llm import BaseLanguageModel
from uglychain.utils import ExtendableEnum as Enum
from uglychain.utils import config

from .baichuan import Baichuan
from .chatgpt import ChatGPT
from .copilot import Copilot
from .custom import Custom
from .dashscope import DashScope
from .gemini import Gemini
from .ollama import Ollama
from .sparkapi import SparkAPI
from .yi import Yi
from .zhipu import ChatGLM


class Model(Enum):
    """
    GPT3_TURBO = "gpt-3.5-turbo"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    COPILOT3_TURBO = "copilot-gpt-3.5-turbo"
    COPILOT4 = "copilot-gpt-4"
    YI = "yi-34b-chat-0205"
    YI_FUNCTION = "yi-34b-chat-creation-v01"
    YI_LONGCONTEXT = "yi-34b-chat-200k-v01"
    BAICHUAN_TURBO = "Baichuan2-Turbo"
    BAICHUAN_TURBO_192K = "Baichuan2-Turbo-192k"
    BAICHUAN_PRO = "Baichuan2-53B"
    CUSTOM = "custom"
    GEMINI = "gemini-pro"
    QWEN = "qwen-max"
    QWEN_LONGCONTEXT = "qwen-max-longcontext"
    QWEN_TURBO = "qwen-turbo"
    QWEN_PLUS = "qwen-plus"
    GLM4 = "glm-4"
    GLM3 = "glm-3-turbo"
    OLLAMA = "ollama"
    SPARK = "v3.5"
    DEFAULT = "default"
    """

    GPT3_TURBO = (ChatGPT, {"model": "gpt-3.5-turbo", "MAX_TOKENS": 16384})
    GPT4 = (ChatGPT, {"model": "gpt-4", "MAX_TOKENS": 8192})
    GPT4_TURBO = (ChatGPT, {"model": "gpt-4-turbo-preview", "MAX_TOKENS": 128000})
    COPILOT3_TURBO = (Copilot, {"model": "gpt-3.5-turbo"})
    COPILOT4 = (Copilot, {"model": "gpt-4"})
    YI = (Yi, {"model": "yi-34b-chat-0205", "MAX_TOKENS": 4096})
    YI_FUNCTION = (Yi, {"model": "yi-34b-chat-creation-v01", "MAX_TOKENS": 16384})
    YI_LONGCONTEXT = (Yi, {"model": "yi-34b-chat-200k-v01", "MAX_TOKENS": 32768})
    BAICHUAN_TURBO = (
        Baichuan,
        {
            "model": "Baichuan2-Turbo",
        },
    )
    BAICHUAN_TURBO_192K = (
        Baichuan,
        {
            "model": "Baichuan2-Turbo-192k",
        },
    )
    BAICHUAN_PRO = (
        Baichuan,
        {
            "model": "Baichuan2-53B",
        },
    )
    CUSTOM = (Custom, {"model": config.custom_model})
    GEMINI = (
        Gemini,
        {
            "model": "gemini-pro",
        },
    )
    QWEN = (DashScope, {"model": "qwen-max", "MAX_TOKENS": 6000})
    QWEN_TURBO = (DashScope, {"model": "qwen-turbo", "MAX_TOKENS": 6000})
    QWEN_PLUS = (DashScope, {"model": "qwen-plus", "MAX_TOKENS": 30000})
    QWEN_LONGCONTEXT = (DashScope, {"model": "qwen-max-longcontext", "MAX_TOKENS": 28000})
    GLM4 = (ChatGLM, {"model": "glm-4", "MAX_TOKENS": 128000})
    GLM3 = (ChatGLM, {"model": "glm-3-turbo", "MAX_TOKENS": 128000})
    OLLAMA = (Ollama, {"model": config.ollama_model})
    SPARK = (
        SparkAPI,
        {
            "model": "v3.5",
        },
    )
    DEFAULT = "default"

    def __call__(self, is_init_delay: bool = False) -> BaseLanguageModel:
        if self == Model.DEFAULT:
            return getattr(Model, config.default_llm.upper(), Model.GPT3_TURBO)(is_init_delay=is_init_delay)
        provider, kwargs = self.value
        kwargs["is_init_delay"] = is_init_delay
        return provider(**kwargs)


'''
LLM_PROVIDERS = {
    Model.GPT3_TURBO: (ChatGPT, {"model": "gpt-3.5-turbo", "MAX_TOKENS": 16384}),
    Model.GPT4: (ChatGPT, {"model": "gpt-4", "MAX_TOKENS": 8192}),
    Model.GPT4_TURBO: (ChatGPT, {"model": "gpt-4-turbo-preview", "MAX_TOKENS": 128000}),
    Model.COPILOT3_TURBO: (Copilot, {"model": "gpt-3.5-turbo"}),
    Model.COPILOT4: (Copilot, {"model": "gpt-4"}),
    Model.YI: (Yi, {"model": "yi-34b-chat-0205", "MAX_TOKENS": 4096, "use_max_tokens": False}),
    Model.YI_FUNCTION: (Yi, {"model": "yi-34b-chat-creation-v01", "MAX_TOKENS": 16384, "use_max_tokens": False, "use_native_tools": True}),
    Model.YI_LONGCONTEXT: (Yi, {"model": "yi-34b-chat-200k-v01", "MAX_TOKENS": 32768, "use_max_tokens": False}),
    Model.BAICHUAN_TURBO: (
        Baichuan,
        {
            "model": "Baichuan2-Turbo",
        },
    ),
    Model.BAICHUAN_TURBO_192K: (
        Baichuan,
        {
            "model": "Baichuan2-Turbo-192k",
        },
    ),
    Model.BAICHUAN_PRO: (
        Baichuan,
        {
            "model": "Baichuan2-53B",
        },
    ),
    Model.CUSTOM: (Custom, {"model": config.custom_model}),
    Model.GEMINI: (
        Gemini,
        {
            "model": "gemini-pro",
        },
    ),
    Model.QWEN: (DashScope, {"model": "qwen-max", "MAX_TOKENS": 6000}),
    Model.QWEN_TURBO: (DashScope, {"model": "qwen-turbo", "MAX_TOKENS": 6000}),
    Model.QWEN_PLUS: (DashScope, {"model": "qwen-plus", "MAX_TOKENS": 30000}),
    Model.QWEN_LONGCONTEXT: (DashScope, {"model": "qwen-max-longcontext", "MAX_TOKENS": 28000}),
    Model.GLM4: (ChatGLM, {"model": "glm-4", "MAX_TOKENS": 128000, "top_p": 0.7}),
    Model.GLM3: (ChatGLM, {"model": "glm-3-turbo", "MAX_TOKENS": 128000, "top_p": 0.7}),
    Model.OLLAMA: (Ollama, {"model": config.ollama_model}),
    Model.SPARK: (
        SparkAPI,
        {
            "model": "v3.5",
        },
    ),
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
'''
