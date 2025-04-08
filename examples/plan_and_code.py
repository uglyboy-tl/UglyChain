from __future__ import annotations

from uglychain import config
from uglychain.tasks import flow, planner
from uglychain.tools import convert_to_tool_list
from uglychain.tools.providers.coder import Coder
from uglychain.tools.providers.default import e2b_mcp_server, execute_command, web_search

config.verbose = True
config.default_model = "openai:gpt-4o"
tools = convert_to_tool_list([e2b_mcp_server, execute_command, web_search, Coder])
tool_descriptions = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
plan = planner("帮我写一个贪吃蛇的网页小游戏", tool_descriptions)
print(plan)
flow(plan.convert_to_task_list(tools))  # type: ignore
