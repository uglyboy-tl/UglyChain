from __future__ import annotations

import http.client
import json
import os
import subprocess
import urllib.parse
from pathlib import Path

from uglychain import Tool

TIMEOUT = 60


def _format_std(stdout: str, stderr: str) -> str:
    output = ""
    if stdout:
        output += f"\n\nSTDOUT:\n{stdout}"
    if stderr:
        output += f"\n\nSTDERR:\n{stderr}"
    return output


@Tool.tool
def execute_command(command: str) -> str:
    """Request to execute a CLI command on the system. Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task. You must tailor your command to the user's system and provide a clear explanation of what the command does. Prefer to execute complex CLI commands over creating executable scripts, as they are more flexible and easier to run. Commands will not be executed in the specified working directory."""

    if not command:
        return "Error: Command cannot be empty."

    working_directory = Path.cwd()
    try:
        result = subprocess.run(
            command, shell=True, cwd=working_directory, capture_output=True, text=True, timeout=TIMEOUT
        )
        if result.returncode == 0:
            return f"Command executed successfully.{_format_std(result.stdout, result.stderr)}"
        else:
            return f"Command execution failed with return code {result.returncode}.{_format_std(result.stdout, result.stderr)}"
    except subprocess.TimeoutExpired:
        return "Command execution timed out after {TIMEOUT} seconds."
    except subprocess.SubprocessError as e:
        return f"Failed to execute command: {str(e)}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


@Tool.tool
def user_input(question: str) -> str:
    """Ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth."""
    try:
        user_input = input(f"{question} => Type your answer here:")
        return user_input
    except Exception as e:
        return f"Failed to ask user: {str(e)}"


@Tool.tool
def web_search(query: str) -> str:
    """Performs a web search based on your query (think a Google search) then returns the top 5 search results."""

    conn = http.client.HTTPSConnection("s.jina.ai")
    # 从环境变量中获取 JINA_API_KEY
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        raise ValueError("JINA_API_KEY is not set")
    # 定义头信息
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Retain-Images": "none",
    }
    body = json.dumps({"q": query})
    # 发送POST请求
    conn.request("POST", "/", body, headers)

    # 获取响应
    response = conn.getresponse()
    data = response.read()
    conn.close()

    # 处理响应
    if response.status == 200:
        return data.decode("utf-8")
    else:
        return f"Failed to fetch webpage. Status code: {response.status}"


@Tool.tool
def visit_webpage(url: str) -> str:
    """Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages."""
    parsed_url = urllib.parse.urlparse(f"https://r.jina.ai/{url}")
    conn = http.client.HTTPSConnection(parsed_url.netloc)

    # 发送GET请求
    conn.request("GET", parsed_url.path or "/")

    # 获取响应
    response = conn.getresponse()
    data = response.read()
    conn.close()

    # 处理响应
    if response.status == 200:
        return data.decode("utf-8")
    else:
        return f"Failed to fetch webpage. Status code: {response.status}"


@Tool.mcp
class e2b_mcp_server:
    command = "npx"
    args = ["-y", "@e2b/mcp-server"]
    env = {"E2B_API_KEY": ""}


__all__ = [
    "execute_command",
    "user_input",
    "web_search",
    "visit_webpage",
    "e2b_mcp_server",
]
