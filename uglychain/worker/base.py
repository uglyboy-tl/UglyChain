#!/usr/bin/env python3

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from uglychain import LLM, Model
from uglychain.retrievers import BaseRetriever

from .storage import Storage

RETRIEVER_PROMPT = """# Context from Retriever(Maybe useful for you to resolve the problem):
---
{retriever_context}
---
"""


@dataclass
class BaseWorker(ABC):
    """Base class for actions.

    Attributes:
        role: The role of the action.
        filename: The filename associated with the action.
        llm: The LLMChain object used for the action.
    """

    role: Optional[str] = None
    prompt: str = "{prompt}"
    model: Model = Model.DEFAULT
    retriever: Optional[BaseRetriever] = None
    storage: Optional[Storage] = None
    llm: Optional[LLM] = field(default=None, init=False)

    def __post_init__(self):
        if self.retriever:
            self.prompt = RETRIEVER_PROMPT + self.prompt

    def _ask(self, *args, **kwargs) -> Any:
        """Ask a question to the LLMChain object.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The response from the LLMChain object.
        """
        assert self.llm, "llm is required"
        response = self.llm(*args, **kwargs)
        return response

    @abstractmethod
    def run(self, *args, **kwargs):
        """Abstract method to be implemented by subclasses.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        if not self.llm:
            self.llm = LLM(self.prompt, self.model, self.role)
        response = self._ask(*args, **kwargs)
        if self.storage:
            self.storage.save(response)
        return response
