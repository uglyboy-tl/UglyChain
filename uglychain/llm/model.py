from enum import Enum
from uglychain.utils import config

class Model(Enum):
    GPT3_TURBO = "gpt-3.5-turbo"
    GPT3_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT4 = "gpt-4"
    GPT4_32K = "gpt-4-32k"
    GPT4_TURBO = "gpt-4-turbo"
    COPILOT3_TURBO = "copilot-3.5"
    COPILOT4 = "copilot-4"
    YI = "yi"
    YI_32K = "yi-32k"
    CUSTOM = "custom"
    QWEN = "qwen"
    QWEN_28K = "qwen-28k"
    QWEN_TURBO = "qwen-turbo"
    QWEN_PLUS = "qwen-plus"
    GLM4 = "glm-4"
    GLM3 = "glm-3"
    DEFAULT = config.llm_provider