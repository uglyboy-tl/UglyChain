from enum import Enum


class Model(Enum):
    GPT3_TURBO = "gpt-3.5-turbo-0125"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    COPILOT3_TURBO = "copilot-gpt-3.5-turbo"
    COPILOT4 = "copilot-gpt-4"
    YI = "yi-34b-chat-creation-v01"
    YI_200K = "yi-34b-chat-200k-v01"
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
    DEFAULT = "default"
