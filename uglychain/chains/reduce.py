#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable, Union

from loguru import logger

from .llm import LLM, GenericResponseType


@dataclass
class ReduceChain(LLM[GenericResponseType]):
    reduce_keys: List[str] = field(default_factory=lambda: ["input"])
    format: Callable[[Union[str, GenericResponseType]], str] = field(
        default_factory=lambda: lambda x: str(x)
    )

    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        self.num = len(inputs[self.reduce_keys[0]])
        for reduce_key in self.reduce_keys:
            self._validate_reduce_key(reduce_key, inputs)
        assert (
            "history" in self.input_keys
        ), "ReduceChain expects response to be in input_keys"
        if not hasattr(inputs, "history"):
            inputs["history"] = ""
        super()._validate_inputs(inputs)

    def _validate_reduce_key(self, reduce_key: str, inputs: Dict[str, Any]) -> None:
        assert (
            reduce_key in self.input_keys
        ), f"ReduceChain expects {reduce_key} to be in input_keys"
        assert isinstance(
            inputs[reduce_key], List
        ), f"ReduceChain expects {reduce_key} to be a list of strings"
        assert (
            len(inputs[reduce_key]) == self.num
        ), f"ReduceChain expects {reduce_key} to be a list of strings with the same length"

    def _call(self, inputs: Dict[str, str]) -> Union[str, GenericResponseType]:
        response = inputs["history"]
        for i in range(self.num):
            response = self._process_input(i, inputs, response)
            logger.debug(f"ReduceChain: {i} finished")
            logger.debug(f"ReduceChain: {response}")
        return response

    def _process_input(
        self, index: int, inputs: Dict[str, str], response: Union[str, GenericResponseType]
    ) -> Union[str, GenericResponseType]:
        new_input = inputs.copy()
        if index > 0:
            new_input.pop("history")
            new_input["history"] = self.format(response)
        new_input.update(
            {reduce_key: inputs[reduce_key][index] for reduce_key in self.reduce_keys}
        )
        return super()._call(new_input)