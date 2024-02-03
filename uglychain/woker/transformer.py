from dataclasses import dataclass
from typing import List, Optional, Union

from uglychain import LLM, MapChain

from .base import BaseWorker

ROLE = """You are an expert Transformer who can help me."""

PROMPT = """Transform the input into {trans_type}.
-----
Input:
{input}"""


@dataclass
class Transformer(BaseWorker):
    role: Optional[str] = ROLE
    prompt: str = PROMPT
    char_limit: int = 1000
    trans_type: str = "Chinese"

    def run(self, input: Union[str, List[str]]):
        if isinstance(input, str) and (not self.llm or isinstance(self.llm, MapChain)):
            self.llm = LLM(self.prompt, self.model, self.role)
        elif isinstance(input, list) and (not self.llm or isinstance(self.llm, LLM)):
            self.llm = MapChain(
                self.prompt,
                self.model,
                self.role,
                map_keys=["input"],
            )
        kwargs = {"input": input, "trans_type": self.trans_type}
        response = self._ask(**kwargs)
        if self.storage:
            self.storage.save(response)
        return response
