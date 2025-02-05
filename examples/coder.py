from __future__ import annotations

from uglychain import config, react
from uglychain.tools.coder import read_file, replace_in_file, write_to_file
from uglychain.tools.default import execute_command


@react("openai:gpt-4o", tools=[read_file, write_to_file, replace_in_file, execute_command])
def coder(task: str):
    return task


if __name__ == "__main__":
    config.verbose = True
    coder("帮我写一个贪吃蛇的网页小游戏")
