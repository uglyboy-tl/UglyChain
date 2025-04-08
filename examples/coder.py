from __future__ import annotations

from uglychain import config, react
from uglychain.tools.providers.coder import Coder
from uglychain.tools.providers.default import execute_command


@react(tools=[Coder, execute_command])
def coder(task: str):
    return task


if __name__ == "__main__":
    config.verbose = True
    coder("帮我写一个贪吃蛇的网页小游戏")
