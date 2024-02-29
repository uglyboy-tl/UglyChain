#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast

from loguru import logger
from yaml import dump

from uglychain.llm import finish, run_function
from uglychain.llm.tools import ActionResopnse, tools_schema

from .llm import LLM, GenericResponseType, Model
from .react import Action
from .react import ReActChain as ReActChainGood

REACT_PROMPT = """
You are designed to help with a variety of tasks, from answering questions to providing summaries to other types of analyses.

## Tools
You have access to a wide variety of tools. You are responsible for using the tools in any sequence you deem appropriate to complete the task at hand. This may require breaking the task into subtasks and using different tools to complete each subtask.

You have access to the following tools:
{tools}

## Output Format
To answer the question, please use the following format.

```
Thought: I need to use a tool to help me answer the question.
Action: tool name (one of {tool_names})
Action Input: the input to the tool, in a JSON format representing the kwargs (e.g. {{"text": "hello world", "num_beams": 5}})
```
Please use a valid JSON format for the action input. Do NOT do this {{'text': 'hello world', 'num_beams': 5}}.

If this format is used, the user will respond in the following format:

```
Observation: tool response
```

You should keep repeating the above format until you have enough information to answer the question without using any more tools. At that point, you MUST respond in the following format:

```
Thought: I can answer without using any more tools.
Action: Finish
Answer: [your answer here]
```

## Current Conversation

Question: {input}
{history}
"""

TRANSFORM_PROMPT_4_YAML = """
Here is a ReAct flow that you will do next
=====
{prompt}
=====
Transform them in the format of output such as:
```yaml
thought: <thought>
action:
  name: <tool name>
  args:
    <tool args>
```
"""

TRANSFORM_PROMPT_4_JSON = """
Here is a ReAct flow that you will do next, transform them in the format of output
=====
{prompt}
=====
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
        self.tools_schema = f"```yaml\n{dump(tools_schema(self.tools), default_flow_style=False)}\n```"
        # self.tools_schema = str(tools_schema(self.tools))
        self.tool_names = ", ".join([f"`{tool.__name__}`" for tool in self.tools])
        self._tools = self.tools
        self._tools.insert(0, finish)
        self.tools = None
        self.stop = "Observation:"
        self.formatchain = LLM(model=self.model, tools=self._tools, response_model=ActionResopnse)
        self.formatchain.llm.use_native_tools = False
        super().__post_init__()
        self.formatchain.prompt = TRANSFORM_PROMPT_4_YAML if self.output_format == "yaml" else TRANSFORM_PROMPT_4_JSON

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
            if len(args) != 1 or not (isinstance(args[0], str) or isinstance(args[0], list)):
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
