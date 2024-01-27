#!/usr/bin/env python3
# -*-coding:utf-8-*-

from typing import Any, Dict, List, Optional, Callable, Tuple, Type, TypeVar, Generic, Union
from dataclasses import dataclass, field

from pydantic import BaseModel
from loguru import logger

from uglychain.provider import get_llm_provider
from uglychain.llm import BaseLanguageModel, Model, ParseError
from ..base import Chain
from .prompt import Prompt

GenericResponseType = TypeVar("GenericResponseType", bound=BaseModel)

@dataclass
class LLM(Chain, Generic[GenericResponseType]):
    """A class representing an LLM chain.

    This class inherits from the Chain class and implements the logic for interacting with a language model.

    Attributes:
        llm_name: The name of the language model.
        prompt_template: The template for the prompt.
    """

    prompt_template: str = "{prompt}"
    model: Model = Model.DEFAULT
    system_prompt: Optional[str] = None
    response_model: Optional[Type[GenericResponseType]] = None
    memory_callback: Optional[Callable[[Tuple[str, str]], None]] = None
    is_init_delay: bool = field(init=False, default=False)
    llm: BaseLanguageModel = field(init=False)

    def __post_init__(self):
        """Initialize the LLMChain object.

        This method initializes the LLMChain object by getting the LLM provider and setting the prompt.
        """
        self.llm = get_llm_provider(self.model.value, self.is_init_delay)
        logger.success(f"{self.model} loaded")
        if self.system_prompt:
            self.llm.set_system_prompt(self.system_prompt)
        self.prompt = self.prompt_template

    @property
    def input_keys(self) -> List[str]:
        """Get the input keys.

        Returns:
            A list of input keys.
        """
        return self.prompt.input_variables

    def _call(self, inputs: Dict[str, Any]) -> Union[GenericResponseType, str]:
        """Call the LLMChain.

        This method calls the LLMChain by formatting the prompt with the inputs and asking the LLM provider.

        Args:
            inputs: A dictionary of inputs.

        Returns:
            The response from the LLM provider.
        """
        prompt = self.prompt.format(**inputs)

        max_retries = 3  # 设置最大重试次数
        attempts = 0     # 初始化尝试次数
        while attempts < max_retries:
            try:
                response = self.llm.generate(prompt, self.response_model)
                if self.response_model:
                    instructor_response = self.llm.parse_response(response, self.response_model)
                    if self.memory_callback:
                        self.memory_callback((prompt, response))
                    return instructor_response
                else:
                    if self.memory_callback:
                        self.memory_callback((prompt, response))
                    return response
            except ParseError as e:  # 捕获所有异常
                attempts += 1       # 尝试次数增加
                logger.warning("解析失败，正在尝试重新解析")
                logger.trace(f"第 {attempts} 次尝试解析失败，原因：{e}")
                if attempts == max_retries:
                    raise e         # 如果达到最大尝试次数，则抛出最后一个异常
            except Exception as e:
                raise e
        raise

    @property
    def prompt(self) -> Prompt:
        """Set the prompt.

        This method sets the prompt using the given prompt template.

        Args:
            prompt_template: The template for the prompt.
        """
        return self._prompt

    @prompt.setter
    def prompt(self, prompt_template: str) -> None:
        """Set the prompt.

        This method sets the prompt using the given prompt template.

        Args:
            prompt_template: The template for the prompt.
        """
        self._prompt = Prompt(prompt_template)
