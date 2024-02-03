#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass, field
from typing import Dict, Union

from loguru import logger

from uglychain.llm import finish, run_function
from uglychain.llm.tools import ActionResopnse

from .llm import LLM, GenericResponseType


@dataclass
class Action:
    thought: str
    action: str
    params: Dict
    obs: str
    current: bool = True

    @property
    def done(self) -> bool:
        if self.action == "finish":
            return True
        else:
            return False

    def __str__(self) -> str:
        return self.info

    @property
    def info(self) -> str:
        if self.done:
            return f"Thought: {self.thought}\nAction: Finish\nObservation: {self.obs}"
        return f"Thought: {self.thought}\nAction: {self.action}\nAction Input: {self.params}\nObservation: {self.obs}"


@dataclass
class ReActChain(LLM[GenericResponseType]):
    llmchain: LLM = field(init=False)

    def __post_init__(self):
        self._acts = []
        # super().__post_init__()
        self.prompt = self.prompt_template
        assert self.tools is not None, "tools must be set"
        self.tools.insert(0, finish)
        self.llmchain = LLM(
            """Question: {input}\n{react_history}""",
            self.model,
            self.system_prompt,
            tools=self.tools,
            response_model=ActionResopnse,
        )
        self.llmchain.llm.use_native_tools = False

    def _call(self, inputs: Dict[str, str]) -> Union[str, GenericResponseType]:
        input = self.prompt.format(**inputs)
        assert self.tools is not None, "tools must be set"
        response = self.llmchain(input=input, react_history="")
        thought = response.thought
        action = response.action.name
        params = response.action.args
        obs = run_function(self.tools, response.action)
        act = Action(thought, action, params, obs)
        logger.success(act.info)
        while not act.done:
            if self._acts:
                self._acts[-1].current = False
            self._acts.append(act)
            react_history = "\n".join(str(a) for a in self._acts)
            # logger.debug(f"{input}\n{react_history}")
            response = self.llmchain(input=input, react_history=react_history)
            thought = response.thought
            action = response.action.name
            params = response.action.args
            obs = run_function(self.tools, response.action)
            act = Action(thought, action, params, obs)
            logger.success(act.info)
        response = obs
        if self.response_model:
            llm = LLM(model=self.model, response_model=self.response_model)
            return llm(response)
        else:
            return response
