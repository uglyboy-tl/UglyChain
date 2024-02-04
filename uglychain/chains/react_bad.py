#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass, field
from typing import Dict, Union

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

{react_history}
"""


@dataclass
class ReActChain(LLM[GenericResponseType]):
    llmchain: LLM = field(init=False)

    def __new__(cls, *args, **kwargs):
        if args and args[1] in [Model.GPT4, Model.GPT4_TURBO, Model.COPILOT4]:
            return ReActChainGood(*args, **kwargs)
        elif kwargs and kwargs.get("model") in [Model.GPT4, Model.GPT4_TURBO, Model.COPILOT4]:
            return ReActChainGood(*args, **kwargs)
        return super().__new__(cls)

    def __post_init__(self):
        self._acts = []
        self.prompt = self.prompt_template
        assert self.tools is not None, "tools must be set"
        self.tools.insert(0, finish)
        self.tools_schema = tools_schema(self.tools)
        self.tool_names = [tool.__name__ for tool in self.tools]

        self.llmchain = LLM(REACT_PROMPT, self.model, self.system_prompt, stop="Observation:")
        self.formatchain = LLM(model=self.model, tools=self.tools, response_model=ActionResopnse)
        self.formatchain.llm.use_native_tools = False

    def _call(self, inputs: Dict[str, str]) -> Union[str, GenericResponseType]:
        input = self.prompt.format(**inputs)
        assert self.tools is not None, "tools must be set"
        react_response = self.llmchain(
            input=input, react_history="", tools=self.tools_schema, tool_names=self.tool_names
        )
        logger.trace(f"{react_response}")
        response = self.formatchain(react_response)
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
            react_response = self.llmchain(
                input=input, react_history=react_history, tools=self.tools_schema, tool_names=self.tool_names
            )
            logger.trace(f"{react_response}")
            response = self.formatchain(react_response)
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
