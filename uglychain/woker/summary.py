from dataclasses import dataclass
from typing import List, Optional, Union

from uglychain import LLM, MapChain

from .base import BaseWorker

ROLE = """You are an expert summarizer and analyzer who can help me.

Generate a concise and coherent summary from the given Context in Chinese.

Condense the context into a well-written summary that captures the main ideas, key points, and insights presented in the context.

Prioritize clarity and brevity while retaining the essential information.

Aim to convey the context's core message and any supporting details that contribute to a comprehensive understanding.

Craft the summary to be self-contained, ensuring that readers can grasp the content even if they haven't read the context.

Provide context where necessary and avoid excessive technical jargon or verbosity.

The goal is to create a summary that effectively communicates the context's content while being easily digestible and engaging.
"""

PROMPT = """Summary should NOT be more than {char_limit} words and make sure that a high school student could understand.

CONTEXT: {input}

SUMMARY:
"""


@dataclass
class Summary(BaseWorker):
    role: Optional[str] = ROLE
    prompt: str = PROMPT
    char_limit: int = 1000

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
            input = [i[:20000] for i in input]  # 20k tokens limit
        kwargs = {"input": input, "char_limit": self.char_limit}
        response = self._ask(**kwargs)
        return response
