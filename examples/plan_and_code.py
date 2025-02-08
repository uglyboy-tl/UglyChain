from __future__ import annotations

from rich.console import Console

from uglychain import config
from uglychain.tasks import flow, planner
from uglychain.tool import convert_to_tools
from uglychain.tools.coder import read_file, replace_in_file, write_to_file
from uglychain.tools.default import e2b_mcp_server, execute_command, web_search

config.verbose = True
config.default_model = "openai:gpt-4o"
tools = convert_to_tools([e2b_mcp_server, execute_command, web_search, read_file, write_to_file, replace_in_file])
tool_descriptions = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
plan = planner("帮我写一个贪吃蛇的网页小游戏", tool_descriptions)
console = Console()
console.print(plan)
flow(plan.convert_to_task_list(tools))  # type: ignore
