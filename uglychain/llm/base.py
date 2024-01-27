#!/usr/bin/env python3
# -*-coding:utf-8-*-

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar, cast

from pydantic import BaseModel
from .instructor import Instructor
from .tool import BaseTool

TEMPERATURE = 0.3
T = TypeVar("T", bound=BaseModel)


@dataclass
class BaseLanguageModel(ABC):
    """Base class for LLM providers.

    This class is an abstract base class (ABC) for LLM providers. It defines the common interface that all LLM providers should implement.

    Attributes:
        delay_init (bool): Whether to delay the initialization of the LLM provider.
        model (str): The model used by the LLM provider.
        use_max_tokens (bool): Whether to use the maximum number of tokens when generating responses.
        client (Any): The client used by the LLM provider.
        temperature (float): The temperature parameter used for generating responses.
        system_prompt (Optional[str]): The system message to be displayed.
        is_continuous (bool): Whether the conversation is continuous.
        messages (list): The list of messages in the conversation.

    Methods:
        set_system_prompt: Set the system message.
        generate: Ask a question and return the user's response.
        completion_with_backoff: Perform completion with backoff.
        _default_params: Get the default parameters for generating responses.
        _create_client: Create the client for the LLM provider.
        _generate_validation: Perform validation before generating responses.
        _generate_messages: Generate the list of messages for the conversation.
        _num_tokens: Calculate the number of tokens in a conversation.
        max_tokens: Get the maximum number of tokens that can be returned at once.
    """

    is_init_delay: bool
    model: str
    client: Any = field(init=False)
    temperature: float = field(init=False, default=TEMPERATURE)
    system_prompt: Optional[str] = field(init=False, default=None)
    use_max_tokens: bool = field(init=False, default=False)
    is_continuous: bool = field(init=False, default=False)
    messages: list = field(init=False, default_factory=list)

    def __post_init__(self):
        if not self.is_init_delay:
            self.client = self._create_client()

    def set_system_prompt(self, msg: Optional[str] = None) -> None:
        """Set the system message.

        Args:
            msg (str, optional): The message to set.

        Returns:
            None

        """
        if msg:
            self.system_prompt = msg

    @abstractmethod
    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[T]] = None,
        tools: Optional[List[BaseTool]] = None,
    ) -> str:
        """Ask a question and return the user's response.

        Args:
            prompt (str, optional): The question prompt.
            response_model (BaseModel, optional): The response model.

        Returns:
            str: The user's response.

        """
        pass

    def parse_response(self, response: str, response_model: Type[T]) -> T:
        """Parse the response from the LLM provider.

        Args:
            response (str): The response from the LLM provider.
            response_model (BaseModel): The response model.

        Returns:
            BaseModel: The parsed response.

        """
        instructor = Instructor.from_BaseModel(response_model)
        return cast(T, instructor.from_response(response))

    @abstractmethod
    def completion_with_backoff(self, **kwargs):
        pass

    @property
    def _default_params(self) -> Dict[str, Any]:
        """Get the default parameters for generating responses.

        Returns:
            Dict[str, Any]: The default parameters.

        """
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
        }
        if self.use_max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        return kwargs

    def _create_client(self):
        """Create the client for the LLM provider.

        Returns:
            Any: The client.

        """
        pass

    def _generate_validation(self):
        """Perform validation before generating responses."""
        if self.is_init_delay:
            self.client = self._create_client()

    def _generate_messages(self, prompt: str) -> List[Dict[str, str]]:
        """Generate the list of messages for the conversation.

        Args:
            prompt (str): The user prompt.

        Returns:
            List[Dict[str, str]]: The list of messages.

        """
        if not self.is_continuous:
            self.messages = []
            if hasattr(self, "system_prompt") and self.system_prompt:
                self.messages.append({"role": "system", "content": self.system_prompt})
        if prompt:
            self.messages.append({"role": "user", "content": prompt})
        return self.messages

    def _num_tokens(self, messages: list, model: str):
        """Calculate the number of tokens in a conversation.

        Args:
            messages (list): The list of messages in the conversation.
            model (str): The model to use for tokenization.

        Returns:
            int: The number of tokens in the conversation.

        """
        return 0

    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Get the maximum number of tokens that can be returned at once.

        Returns:
            int: The maximum number of tokens.

        """
        pass
