from dataclasses import dataclass

from uglychain.utils import config
from .openai_api import ChatGPTAPI


@dataclass
class Baichuan(ChatGPTAPI):
    api_key: str = config.baichuan_api_key
    base_url: str = "https://api.baichuan-ai.com/v1"
    name: str = "Baichuan"
    use_max_tokens: bool = False
