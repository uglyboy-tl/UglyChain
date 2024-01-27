from dataclasses import dataclass

from .openai_api import ChatGPTAPI

from uglychain.utils import config


@dataclass
class Copilot(ChatGPTAPI):
    api_key: str = config.copilot_token
    base_url: str = config.copilot_gpt4_service_url
    name: str = "Github Copilot"
    use_max_tokens: bool = False
