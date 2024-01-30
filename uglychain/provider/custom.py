from dataclasses import dataclass

from uglychain.utils import config

from .openai_api import ChatGPTAPI


@dataclass
class Custom(ChatGPTAPI):
    api_key: str = config.custom_token
    base_url: str = config.custom_url
    model: str = config.custom_model
    name: str = "CUSTOM"
    use_max_tokens: bool = False
