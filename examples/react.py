from __future__ import annotations

import os
import platform
from pathlib import Path

from examples.schema import get_current_weather, search_baidu
from pydantic import BaseModel

from uglychain import config, react
from uglychain.utils import execute_command

SYSTEM_INFORMATION = f"""====
SYSTEM INFORMATION

Operating System: {platform.system()}
Default Shell: {os.environ.get("SHELL")}
Home Directory: {os.environ.get("HOME")}
Current Working Directory: {str(Path.cwd().absolute)}"""
""""""


class Date(BaseModel):
    year: int


@react("openai:gpt-4o-mini", [get_current_weather, search_baidu], response_format=Date)
def test():
    return "牛顿生于哪一年？"


@react("openai:gpt-4o-mini", [execute_command])
def update():
    return "更新我的电脑系统"


if __name__ == "__main__":
    config.verbose = True
    print(test())
    # update()
