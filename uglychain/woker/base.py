#!/usr/bin/env python3
# -*-coding:utf-8-*-

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from uglychain import LLM, Model

from .storage import Storage


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
    storage: Optional[Storage] = None
    llm: Optional[LLM] = None

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
