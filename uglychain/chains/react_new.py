#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Union

from loguru import logger

from .llm import LLM, FunctionCall, GenericResponseType


def final_answer(response: str)-> str:
    """the final answer tool must be used to respond to the user. You must use this when you have decided on an answer.

    Args:
        response (str): The response to return.
    """
    return response

def call(tools: List[Callable], response: FunctionCall):
    for tool in tools:
        if tool.__name__ == response.name:
            return tool(**response.args)
    raise ValueError(f"Can't find tool {response.name}")

@dataclass
class Action:
    thought: str
    action: str
    params: Dict
    obs: str
    current: bool = True

    @property
    def done(self) -> bool:
        if self.action == "final_answer":
            return True
        else:
            return False

    def __str__(self) -> str:
        return self.info

    @property
    def info(self) -> str:
            return f"Thought: {self.thought}\nAction: {self.action}\nAction Input: {self.params}\nObservation: {self.obs}"

@dataclass
class ReActChain(LLM[GenericResponseType]):
    reactllm: LLM = field(init=False)

    def __post_init__(self):
        self._acts = []
        super().__post_init__()
        assert self.tools is not None, "tools must be set"
        self.tools.insert(0, final_answer)
        self.reactllm = LLM("""Question: {input}\n{react_history}""",self.model, tools=self.tools)

    def _call(self, inputs: Dict[str, str]) -> Union[str, GenericResponseType]:
        input = self.prompt.format(**inputs)
        response = self.reactllm(input = input, react_history = "")
        thought = response.thought
        action = response.name
        params = response.args
        obs = call(self.tools, response) # type: ignore
        act = Action(thought, action, params, obs)
        logger.success(act.info)
        while not act.done:
            if self._acts:
                self._acts[-1].current = False
            self._acts.append(act)
            react_history = "\n".join(str(a) for a in self._acts) + "\n\nWhat do you think to do next? Don't repeat yourself."
            logger.debug(f"{input}\n{react_history}")
            response = self.reactllm(input = input, react_history = react_history)
            thought = response.thought
            action = response.name
            params = response.args
            obs = call(self.tools, response) # type: ignore
            act = Action(thought, action, params, obs)
            logger.success(act.info)
        response = act.params["response"]
        if self.response_model:
            llm = LLM(model=self.model, response_model=self.response_model)
            return llm(response)
        else:
            return response