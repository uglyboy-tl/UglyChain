from enum import Enum

from uglychain.llm import BaseLanguageModel
from uglychain.utils import config, inheritable_enum

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


@inheritable_enum
class Model(Enum):
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
