from __future__ import annotations

import textwrap
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property

from ..config import config
from ..llm import llm
from ..react import react
from ..react.action import Action
from ..schema import Messages
from ..tools import Tools, convert_to_tool_list, get_tools_descriptions
from .prompt import INITIAL_PLAN, UPDATE_PLAN_SYSTEM, UPDATE_PLAN_USER

PLANNING_INTERVAL = 6
MAX_STEPS = 30


@llm("deepseek:deepseek-chat", stop="<end_plan>")
def create_planning(task: str, tools_descriptions: str) -> str:
    return INITIAL_PLAN.format(
        task=task,
        tools_descriptions=tools_descriptions,
        managed_agents_descriptions="",
        language=config.default_language,
    )


@llm(
    "deepseek:deepseek-chat",
    stop="<end_plan>",
)
def update_planning(
    acts: list[Action], task: str, remaining_steps: int, tools_descriptions: str
) -> list[dict[str, str]]:
    system_prompt = UPDATE_PLAN_SYSTEM.format(task=task)
    messages: Messages = [{"role": "system", "content": system_prompt}]
    for act in acts:
        messages.append({"role": "assistant", "content": str(act)})
    messages.append(
        {
            "role": "user",
            "content": UPDATE_PLAN_USER.format(
                remaining_steps=remaining_steps if remaining_steps > 0 else "Unlimited",
                tools_descriptions=tools_descriptions,
                managed_agents_descriptions="",
                language=config.default_language,
            ),
        }
    )
    return messages


@dataclass
class Plan:
    task: str
    tools: Tools
    model: str = field(default=config.default_model)
    planning_interval: int = field(default=PLANNING_INTERVAL)
    max_steps: int = field(default=MAX_STEPS)
    is_first_time: bool = field(init=False, default=True)
    _memory_message: Messages = field(init=False, default_factory=list)

    @cached_property
    def tools_descriptions(self) -> str:
        return get_tools_descriptions(convert_to_tool_list(self.tools))

    def get_init_plan(self) -> str:
        plan = textwrap.dedent(
            f"""I still need to solve the task I was given:\n```\n{self.task}\n```\n\nHere are the facts I know and my new/updated plan of action to solve the task:\n```\n{create_planning(self.task, self.tools_descriptions)}\n```"""
        )
        return plan

    def get_update_plan(self, acts: list[Action], remaining_steps: int) -> str:
        plan = textwrap.dedent(
            f"""I still need to solve the task I was given:\n```\n{self.task}\n```\n\nHere are the facts I know and my new/updated plan of action to solve the task:\n```\n{update_planning(acts, self.task, remaining_steps, self.tools_descriptions)}\n```"""
        )
        return plan

    @cached_property
    def react(self) -> Callable[[Messages], list[Action]]:
        def main(messages: Messages) -> Messages:
            return messages

        return react(self.model, tools=self.tools, response_format=list[Action], max_steps=self.planning_interval)(main)

    def gen_messages(self, acts: list[Action] | None = None, remaining_steps: int = -1) -> Messages:
        messages: Messages = []
        if acts is None:
            acts = []
        plan: str
        if self.is_first_time:
            plan = self.get_init_plan()
            self.is_first_time = False
        else:
            plan = self.get_update_plan(acts, remaining_steps)
        messages.append({"role": "assistant", "content": plan})
        messages.append({"role": "user", "content": "Now proceed and carry out this plan."})
        for act in acts:
            self._memory_message.append({"role": "assistant", "content": str(act)})
        self._memory_message.extend(messages)
        return self._memory_message

    def process(self) -> str:
        remaining_steps = self.max_steps
        history: list[Action] = []
        acts = self.react(self.gen_messages())

        while not acts[-1].done:
            remaining_steps -= len(acts)
            history.extend(acts)
            acts = self.react(self.gen_messages(acts, remaining_steps))

        return acts[-1].obs
