#!/usr/bin/env python3

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from loguru import logger
from pydantic import BaseModel

from .instructor import Instructor
from .tools import FUNCTION_CALL_FORMAT, FUNCTION_CALL_WITH_FINISH_FORMAT, FunctionCall, finish, tools_schema

TEMPERATURE = 0.3
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0
TOP_P = 1
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
    top_p: float = field(init=False, default=TOP_P)
    frequency_penalty: float = field(init=False, default=FREQUENCY_PENALTY)
    presence_penalty: float = field(init=False, default=PRESENCE_PENALTY)
    system_prompt: Optional[str] = field(init=False, default=None)
    use_max_tokens: bool = field(init=False, default=False)
    seed: int = field(init=False, default=random.getrandbits(16))
    is_continuous: bool = field(init=False, default=False)
    messages: list = field(init=False, default_factory=list)
    use_native_tools: bool = field(init=False, default=False)

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
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> Any:
        """Ask a question and return the user's response.

        Args:
            prompt (str, optional): The question prompt.
            response_model (BaseModel, optional): The response model.

        Returns:
            str: The user's response.

        """
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        response = self.completion_with_backoff(**kwargs)
        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response

    def get_kwargs(
        self,
        prompt: str,
        response_model: Optional[Type[T]],
        tools: Optional[List[Callable]],
        stop: Union[Optional[str], List[str]],
    ) -> Dict[str, Any]:
        self._generate_validation()
        if tools:
            if not response_model:
                response_model = cast(Type[T], FunctionCall)
            try:
                index = tools.index(finish)
                tools[:] = [tools[index]] + tools[:index] + tools[index + 1 :]
                tool_names = ", ".join([f"`{tool.__name__}`" for tool in tools])
                prompt += f"\n{FUNCTION_CALL_WITH_FINISH_FORMAT.format(tool_names = tool_names, tool_schema = tools_schema(tools))}"
            except ValueError:
                tool_names = ", ".join([f"`{tool.__name__}`" for tool in tools])
                prompt += f"\n{FUNCTION_CALL_FORMAT.format(tool_names = tool_names, tool_schema = tools_schema(tools))}"
        if response_model:
            instructor = Instructor.from_BaseModel(response_model)
            prompt += "\n" + instructor.get_format_instructions()
        self._generate_messages(prompt)
        if stop and isinstance(stop, str):
            stop = [stop]
        kwargs = {"messages": self.messages, "stop": stop, **self.default_params}
        return kwargs

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
    def default_params(self) -> Dict[str, Any]:
        """Get the default parameters for generating responses.

        Returns:
            Dict[str, Any]: The default parameters.

        """
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "seed": self.seed,
        }
        if self.use_max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        return kwargs

    @abstractmethod
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
