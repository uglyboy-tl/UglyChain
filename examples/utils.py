from __future__ import annotations

import shlex
import subprocess
from pathlib import Path


def execute_command(command: str) -> str:
    """
    Request to execute a CLI command on the system. Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task. You must tailor your command to the user's system and provide a clear explanation of what the command does. Prefer to execute complex CLI commands over creating executable scripts, as they are more flexible and easier to run. Commands will be executed in the specified working directory.
    """

    if not command:
        raise ValueError("Command cannot be empty")

    working_directory = Path.cwd()

    result = subprocess.run(shlex.split(command), cwd=working_directory, capture_output=True, text=True)
    return result.stdout + result.stderr


def read_file(path: str) -> str:
    "Request to read the contents of a file at the specified path. Use this when you need to examine the contents of an existing file you do not know the contents of, for example to analyze code, review text files, or extract information from configuration files. Automatically extracts raw text from PDF and DOCX files. May not be suitable for other types of binary files, as it returns the raw content as a string."
    _path = Path(path)
    if not _path.exists():
        raise FileNotFoundError(f"File {path} not found.")
    with _path.open("rb") as f:
        return str(f.read())


def write_to_file(path: str, content: str) -> None:
    "Description: Request to write content to a file at the specified path. If the file exists, it will be overwritten with the provided content. If the file doesn't exist, it will be created. This tool will automatically create any directories needed to write the file."
    _path = Path(path)
    _path.parent.mkdir(parents=True, exist_ok=True)
    with _path.open("w") as f:
        f.write(content)
