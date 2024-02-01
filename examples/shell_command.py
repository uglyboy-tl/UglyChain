import platform
import subprocess
import sys
from pathlib import Path
from typing import Callable, List

from loguru import logger

from uglychain import Model

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")


def command(shell: str, cwd: str = "") -> str:
    """
    Executes a shell command and returns the output.

    Args:
        shell (str): The shell command to be executed.
        cwd (str, optional): The current working directory for the command execution. Defaults to "".
    """
    if cwd == "":
        cwd = None  # type: ignore
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                f"powershell -Command '{shell}'",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
            )
        else:
            result = subprocess.run(
                f"set -o pipefail; {shell}",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                executable="/bin/bash",
                cwd=cwd,
            )
        output = result.stdout.decode().strip()
        if output != "":
            return output
        else:
            return "Command executed successfully."
    except subprocess.CalledProcessError as e:
        logger.warning(e.stderr.decode())
        return "Command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)


ROLE = """
假设你是一名系统运维工程师，你正在操作的系统版本为 {os_version}，你当前的目录是 `{cwd}` 。为了达到这个目标，你需要依次执行一系列的命令行指令。请一步步地描述你的解决方案，每一步都应该对应一个命令行指令（请不要在一次操作中执行多个命令）。你需要根据每次指令的执行结果来调整你的下一步操作。请注意，你只能通过命令行来完成你的目标，不能使用图形界面。请将已获得的执行结果融入你的解决方案中，以不断完善你的解决方案。你的输出应该只包含下一步将执行的命令行指令。请确保你的命令能够自动执行，不需要人工干预，所以不要使用 `su root` 这样的交互式命令。如果需要 root 权限，请使用 `sudo` 执行。如果你的命令行指令需要在特定的目录下执行，请直接给出执行的目录。如果需要执行文件操作，请使用 sed、awk、grep 等命令行工具，或者通过 echo 重定向的方式。因为你能获取的信息有字数限制，所以努力让命令行指令执行的结果尽可能精简。回答请使用中文。
"""


def react(model: Model | None = None):
    tools: List[Callable] = [command]
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

        llm = ReActChain(system_prompt=ROLE.format(os_version=platform.system(), cwd=Path.cwd()), tools=tools)

    response = llm("更新系统的软件包。")
    # response = llm("What's the weather in San Francisco?")
    logger.info(response)


if __name__ == "__main__":
    react(Model.YI_32K)