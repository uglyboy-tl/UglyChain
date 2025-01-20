from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from .llm import llm


def final_answer(answer: str) -> str:
    """When get Final Answer, use this tool to return the answer and finishes the task."""
    return answer


def user_input(question: str) -> str:
    """
    Asks for user's input on a specific question
    """
    user_input = input(f"{question} => Type your answer here:")
    return user_input


@llm
def chat(question: str) -> str:
    """
    You are a helpful assistant. You are designed to answer questions for users.
    """
    return f"{question}"


chat.__doc__ = """
Get the answer to the question input from Large Language Models.
"""


def execute_command(command: str) -> str:
    """
    Request to execute a CLI command on the system. Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task. You must tailor your command to the user's system and provide a clear explanation of what the command does. Prefer to execute complex CLI commands over creating executable scripts, as they are more flexible and easier to run. Commands will be executed in the specified working directory.
    """

    if not command:
        raise ValueError("Command cannot be empty")

    working_directory = Path.cwd()

    result = subprocess.run(shlex.split(command), cwd=working_directory, capture_output=True, text=True)
    return result.stdout + result.stderr


__all__ = [
    "final_answer",
    "execute_command",
    "user_input",
    "chat",
]
