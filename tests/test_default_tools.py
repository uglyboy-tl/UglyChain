from __future__ import annotations

import os
import sys
from io import StringIO
from pathlib import Path

from uglychain.client import Client
from uglychain.default_tools import chat, execute_command, final_answer, user_input


def load_env_file(filepath):
    path = Path(filepath)
    with path.open() as f:
        for line in f:
            # 去除空行和注释
            if line.strip() and not line.startswith("#"):
                # 拆分键和值
                key, value = line.strip().split("=", 1)
                # 设置环境变量
                os.environ[key] = value
                print(f"{key} = {value}")


def test_final_answer():
    assert final_answer("Test Answer") == "Test Answer"


def test_user_input():
    input_str = "Test Input"
    sys.stdin = StringIO(input_str)
    assert user_input("Test Question") == input_str
    sys.stdin = sys.__stdin__


"""
def test_chat():
    Client.reset()
    # 加载 .env 文件
    load_env_file(".env")
    assert chat("Test Question")
"""


def test_execute_command():
    result = execute_command("echo Hello World")
    assert "Hello World" in result
