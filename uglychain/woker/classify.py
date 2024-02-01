from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Union

from pydantic import BaseModel

from uglychain import LLM, MapChain

from .base import BaseWorker

PROMPT = """请对下面的文本进行分类：
```text
{input}
```
{samples}
"""


@dataclass
class Classify(BaseWorker):
    prompt: str = PROMPT
    label: Optional[Type[BaseModel]] = None
    samples: Optional[Dict[str, str]] = None
    samples_prompt: str = field(init=False, default="")

    def __post_init__(self):
        assert self.label, "classify_response is required"
        if self.samples:
            self.samples_prompt = "Here is some samples:\n"
            for label, sample in self.samples.items():
                self.samples_prompt += f"`{sample}` will be classified as: {label}\n"

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
        kwargs = {"input": input, "samples": self.samples_prompt}
        response = self._ask(**kwargs)
        return response