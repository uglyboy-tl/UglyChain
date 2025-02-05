from __future__ import annotations

from uglychain import config, react
from uglychain.tools.coder import read_file, replace_file, write_file
from uglychain.tools.default import execute_command


@react("openai:gpt-4o", tools=[read_file, write_file, replace_file, execute_command])
def coder(task: str):
    return task


if __name__ == "__main__":
    config.verbose = True
    coder("帮我看看 bspwm 的配置文件(~/.config/bspwm/bspwmrc)有什么值得优化的地方")
