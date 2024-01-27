from dataclasses import dataclass

from .openai_api import ChatGPTAPI

from uglychain.utils import config


@dataclass
class Custom(ChatGPTAPI):
    api_key: str = config.custom_token
    base_url: str = config.custom_url
    model: str = config.custom_model
    name: str = "CUSTOM"
    use_max_tokens: bool = False
