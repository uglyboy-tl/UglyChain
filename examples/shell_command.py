from __future__ import annotations

import platform
import sys
from collections.abc import Callable
from pathlib import Path

from loguru import logger

from uglychain import Model
from uglychain.tools import run_code

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")

ROLE = """
假设你是一名系统运维工程师，你正在操作的系统版本为 {os_version} 。 你需要在用户的电脑上执行命令。为了完成目标，你需要依次执行一系列的命令行指令。请一步步地描述你的解决方案，每一步都应该对应一个命令行指令（请不要在一次操作中执行多个命令）。你需要根据每次指令的执行结果来调整你的下一步操作。请将已获得的执行结果融入你的解决方案中，以不断完善你的解决方案。你的输出应该只包含下一步将执行的命令行指令。回答请使用中文。
"""


def react(model: Model | None = None):
    tools: list[Callable] = [run_code]
    system_prompt = ROLE.format(os_version=platform.system())
    if model:
        if model in {Model.GPT4_TURBO, Model.GLM4}:
            from uglychain.chains.react import ReActChain
        else:
            from uglychain.chains.react_bad import ReActChain
        llm = ReActChain(
            system_prompt=ROLE.format(os_version=platform.system(), cwd=Path.cwd()), model=model, tools=tools
        )
    else:
        from uglychain.chains.react_bad import ReActChain

        llm = ReActChain(system_prompt=system_prompt, tools=tools)

    response = llm("更新系统软件包")
    # response = llm("What's the weather in San Francisco?")
    logger.info(response)


if __name__ == "__main__":
    react(Model.YI)
