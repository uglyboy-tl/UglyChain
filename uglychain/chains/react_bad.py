#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast

from loguru import logger

from uglychain.llm import Model, finish, run_function
from uglychain.llm.tools import ActionResopnse, tools_schema

from .llm import LLM, GenericResponseType
from .react import Action
from .react import ReActChain as ReActChainGood

REACT_PROMPT = """
Assistant is a large language model trained by Human.

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

TOOLS:
------

Assistant has access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

New input:
{input}

{history}
"""


@dataclass
class ReActChain(LLM[GenericResponseType]):
    max_reacts: int = 3
    _response_model: Optional[Type[GenericResponseType]] = field(init=False, default=None)
    _prompt_template: str = field(init=False)
    _tools: List[Callable] = field(init=False)
    formatchain: LLM = field(init=False)
    tools_schema: str = field(init=False)
    tool_names: str = field(init=False)

    def __new__(cls, *args, **kwargs):
        if args and args[1] in [Model.GPT4, Model.GPT4_TURBO, Model.COPILOT4]:
            return ReActChainGood(*args, **kwargs)
        elif kwargs and kwargs.get("model") in [Model.GPT4, Model.GPT4_TURBO, Model.COPILOT4]:
            return ReActChainGood(*args, **kwargs)
        return super().__new__(cls)

    def __post_init__(self):
        self._acts = []
        assert self.tools is not None, "tools must be set"
        self._prompt_template = self.prompt_template
        self.prompt_template = REACT_PROMPT.replace("{input}", self.prompt_template)
        self._response_model = self.response_model
        self.response_model = None
        self.tools_schema = str(tools_schema(self.tools))
        self.tool_names = ", ".join([f"`{tool.__name__}`" for tool in self.tools])
        self._tools = self.tools
        self._tools.insert(0, finish)
        self.tools = None
        self.stop = "Observation:"
        super().__post_init__()
        self.formatchain = LLM(model=self.model, tools=self._tools, response_model=ActionResopnse)
        self.formatchain.llm.use_native_tools = False

    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        assert "tools" in self.input_keys, "ReduceChain expects history to be in input_keys"
        assert "tool_names" in self.input_keys, "ReduceChain expects history to be in input_keys"
        assert "history" in self.input_keys, "ReduceChain expects history to be in input_keys"
        if "history" not in inputs:
            inputs["history"] = ""
        if "tools" not in inputs:
            inputs["tools"] = self.tools_schema
        if "tool_names" not in inputs:
            inputs["tool_names"] = self.tool_names
        super()._validate_inputs(inputs)

    def _check_args_kwargs(self, args: Any, kwargs: Any) -> Dict[str, Any]:
        if args and not kwargs:
            if len(args) != 1 or not isinstance(args[0], Union[str, list]):
                raise ValueError("`run` supports only one positional argument of type str or list.")
            return {self.input_keys[2]: args[0]}
        return super()._check_args_kwargs(args, kwargs)

    def _call(self, inputs: Dict[str, str]) -> Union[str, GenericResponseType]:
        react_response = self._process(inputs=inputs, history="")
        logger.trace(f"{react_response}")
        response = self.formatchain(react_response)
        thought = response.thought
        action = response.action.name
        params = response.action.args
        obs = run_function(self._tools, response.action)
        act = Action(thought, action, params, obs)
        logger.success(act.info)
        react_times = 0
        while not act.done and react_times < self.max_reacts:
            if self._acts:
                self._acts[-1].current = False
            self._acts.append(act)
            react_history = "\n".join(str(a) for a in self._acts)
            react_response = self._process(inputs=inputs, history=react_history)
            logger.trace(f"{react_response}")
            response = self.formatchain(react_response)
            thought = response.thought
            action = response.action.name
            params = response.action.args
            obs = run_function(self._tools, response.action)
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
