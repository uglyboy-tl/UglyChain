#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type, Union, cast

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
    max_reacts: int = 3
    _response_model: Optional[Type[GenericResponseType]] = field(init=False, default=None)
    _prompt_template: str = field(init=False)

    def __post_init__(self):
        self._acts = []
        assert self.tools is not None, "tools must be set"
        self._prompt_template = self.prompt_template
        self.prompt_template = f"Question: {self.prompt_template}\n{{history}}"
        self._response_model = self.response_model
        self.response_model = ActionResopnse  # type: ignore
        self.tools.insert(0, finish)
        super().__post_init__()
        # self.prompt = self.prompt_template
        self.llm.use_native_tools = False

    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        assert "history" in self.input_keys, "ReduceChain expects history to be in input_keys"
        if "history" not in inputs:
            inputs["history"] = ""
        super()._validate_inputs(inputs)

    def _call(self, inputs: Dict[str, str]) -> Union[str, GenericResponseType]:
        assert self.tools is not None, "tools must be set"
        response = self._process(inputs=inputs, history="")
        thought = response.thought
        action = response.action.name
        params = response.action.args
        obs = run_function(self.tools, response.action)
        act = Action(thought, action, params, obs)
        logger.success(act.info)
        react_times = 0
        while not act.done and react_times < self.max_reacts:
            if self._acts:
                self._acts[-1].current = False
            self._acts.append(act)
            react_history = "\n".join(str(a) for a in self._acts)
            response = self._process(inputs=inputs, history=react_history)
            thought = response.thought
            action = response.action.name
            params = response.action.args
            obs = run_function(self.tools, response.action)
            act = Action(thought, action, params, obs)
            logger.success(act.info)
            react_times += 1
        response = obs
        if not act.done and react_times >= self.max_reacts:
            logger.warning(f"ReAct times {react_times} >= max_ReActs {self.max_reacts}")
            llm = LLM(
                "Question:{prompt}\n-----\n{history}\n-----\n Now you must give an answer!",
                self.model,
                response_model=self._response_model,
            )
            prompt = self._prompt_template.format(**inputs)
            history = "\n".join(str(a) for a in self._acts)
            return llm(prompt=prompt, history=history)
        if self._response_model:
            llm = LLM("{prompt}", self.model, response_model=self._response_model)
            return llm(response)
        else:
            return response

    def _process(self, inputs: Dict[str, str], history: str) -> ActionResopnse:
        new_input = inputs.copy()
        new_input["history"] = history
        response = super()._call(new_input)
        return cast(ActionResopnse, response)
