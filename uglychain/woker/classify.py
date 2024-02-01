from dataclasses import dataclass
from typing import Dict, List, Optional, Type, Union

from pydantic import BaseModel

from uglychain import LLM, MapChain

from .base import BaseWorker

PROMPT = """请对下面的文本进行分类：
```text
{input}
```
"""


@dataclass
class Classify(BaseWorker):
    prompt: str = PROMPT
    label: Optional[Type[BaseModel]] = None
    samples: Optional[Dict[str, str]] = None

    def __post_init__(self):
        assert self.label, "classify_response is required"
        if self.samples:
            prompt = "Here is some samples:\n"
            for label, sample in self.samples.items():
                prompt += f"`{sample}` will be classified as: {label}\n"
            self.prompt = self.prompt + prompt

    def run(self, input: Union[str, List[str]]):
        if isinstance(input, str) and (not self.llm or isinstance(self.llm, MapChain)):
            self.llm = LLM(self.prompt, self.model, self.role, self.label)
        elif isinstance(input, list) and (not self.llm or isinstance(self.llm, LLM)):
            self.llm = MapChain(
                self.prompt,
                self.model,
                self.role,
                self.label,
                map_keys=["input"],
            )
        kwargs = {"input": input}
        response = self._ask(**kwargs)
        return response
