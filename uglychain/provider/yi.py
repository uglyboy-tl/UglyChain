from dataclasses import dataclass

from uglychain.utils import config

from .openai_api import ChatGPTAPI


@dataclass
class Yi(ChatGPTAPI):
    api_key: str = config.yi_api_key
    base_url: str = "https://api.01ww.xyz/v1"
    name: str = "Yi"
    use_max_tokens: bool = False
