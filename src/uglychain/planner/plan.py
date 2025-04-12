from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from functools import cached_property

from examples.mcp_tool import amap_mcp_server, thinking_mcp_server

from uglychain import llm
from uglychain.planner.prompt import INITIAL_PLAN, UPDATE_PLAN_SYSTEM, UPDATE_PLAN_USER
from uglychain.schema import Messages
from uglychain.tools import Tools, convert_to_tool_list, get_tools_descriptions
from uglychain.tools.providers.coder import Coder
from uglychain.tools.providers.default import e2b_mcp_server, execute_command, web_search


@llm("deepseek:deepseek-chat", stop="<end_plan>")
def create_planning(task: str, tools_descriptions: str) -> str:
    return INITIAL_PLAN.format(task=task, tools_descriptions=tools_descriptions, managed_agents_descriptions="")


@llm(
    "deepseek:deepseek-chat",
    stop="<end_plan>",
)
def update_planning(
    messages_history: list[dict[str, str]], task: str, remaining_steps: int, tools_descriptions: str
) -> list[dict[str, str]]:
    system_prompt = UPDATE_PLAN_SYSTEM.format(task=task)
    messages = messages_history.copy()
    if not messages or messages[0]["role"] != "system":
        messages.insert(0, {"role": "system", "content": system_prompt})
    elif messages[0]["role"] == "system":
        messages[0]["content"] = system_prompt
    messages.append(
        {
            "role": "user",
            "content": UPDATE_PLAN_USER.format(
                remaining_steps=remaining_steps, tools_descriptions=tools_descriptions, managed_agents_descriptions=""
            ),
        }
    )
    return messages


@dataclass
class Plan:
    task: str
    tools: Tools
    is_first_time: bool = field(init=False, default=True)

    @cached_property
    def tools_descriptions(self) -> str:
        return get_tools_descriptions(convert_to_tool_list(self.tools))

    def get_init_plan(self) -> str:
        plan = textwrap.dedent(
            f"""I still need to solve the task I was given:\n```\n{task}\n```\n\nHere are the facts I know and my new/updated plan of action to solve the task:\n```\n{create_planning(task, self.tools_descriptions)}\n```"""
        )
        return plan

    def gen_messages(self, messages: Messages, remaining_steps: int) -> Messages:
        plan: str
        if self.is_first_time:
            plan = self.get_init_plan()
            self.is_first_time = False
        else:
            plan = self.get_update_plan(messages, remaining_steps)
        messages.append({"role": "assistant", "content": plan})
        messages.append({"role": "user", "content": "Now proceed and carry out this plan."})
        return messages

    def get_update_plan(self, messages: Messages, remaining_steps: int) -> str:
        plan = textwrap.dedent(
            f"""I still need to solve the task I was given:\n```\n{task}\n```\n\nHere are the facts I know and my new/updated plan of action to solve the task:\n```\n{update_planning(messages, self.task, remaining_steps, self.tools_descriptions)}\n```"""
        )
        return plan


if __name__ == "__main__":
    # task = "帮我做一个上海一日游的规划(使用中文)"
    task = "帮我写一个贪吃蛇的网页小游戏(使用中文)"
    tools: Tools = [amap_mcp_server, thinking_mcp_server, e2b_mcp_server, execute_command, web_search, Coder]  # type: ignore

    plan = Plan(task, tools)
    print(plan.get_init_plan())
