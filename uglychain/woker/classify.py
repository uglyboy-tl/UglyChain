from dataclasses import dataclass
from enum import Enum
from typing import Dict, Generic, List, Literal, Optional, Type, TypeVar, Union

from pydantic import BaseModel, Field

from uglychain import LLM, MapChain

from .base import BaseWorker

LABEL = TypeVar("LABEL", bound=Enum)


class ClassifyResponse(BaseModel, Generic[LABEL]):
    reason: str = Field(..., description="The reason to explain the classification.")
    label: LABEL = Field(..., description="The label of the classification.")


PROMPT = """请对下面的文本进行分类：
```text
{input}
```
"""


@dataclass
class Classify(BaseWorker, Generic[LABEL]):
    prompt: str = PROMPT
    # lable: Optional[Type[LABEL]] = None
    classify_response: Optional[Type[BaseModel]] = None
    samples: Optional[Dict[LABEL, str]] = None

    def __post_init__(self):
        assert self.classify_response, "classify_response is required"
        if self.samples:
            prompt = "These are the samples:\n"
            for label, sample in self.samples.items():
                prompt += f"`{sample}` will be classified as: {label}\n"
            self.prompt = self.prompt + prompt

    def run(self, input: Union[str, List[str]]):
        if isinstance(input, str) and (not self.llm or isinstance(self.llm, MapChain)):
            self.llm = LLM(self.prompt, self.model, self.role, self.classify_response)
        elif isinstance(input, list) and (not self.llm or isinstance(self.llm, LLM)):
            self.llm = MapChain(
                self.prompt,
                self.model,
                self.role,
                self.classify_response,
                map_keys=["input"],
            )
        kwargs = {"input": input}
        response = self._ask(**kwargs)
        return response
