from __future__ import annotations

from examples.mcp_tool import amap_mcp_server

from uglychain import Tools, config
from uglychain.plan import Plan

# from uglychain.tools.providers.coder import Coder
from uglychain.tools.providers.default import e2b_mcp_server, execute_command, web_search

if __name__ == "__main__":
    config.verbose = True
    # task = "帮我做一个上海一日游的规划"
    # task = "帮我写一个贪吃蛇的网页小游戏"
    task = "我的操作系统是 Debian。帮我更新我的软件包"
    # tools: Tools = [amap_mcp_server, thinking_mcp_server, e2b_mcp_server, execute_command, web_search, Coder]  # type: ignore
    tools: Tools = [execute_command, amap_mcp_server]
    plan = Plan(task, tools)

    plan.process()
