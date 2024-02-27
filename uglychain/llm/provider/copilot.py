from dataclasses import dataclass

from uglychain.utils import config

from .openai_api import ChatGPTAPI


@dataclass
class Copilot(ChatGPTAPI):
    api_key: str = config.copilot_token
    base_url: str = config.copilot_gpt4_service_url
    name: str = "Github Copilot"
    use_max_tokens: bool = False
