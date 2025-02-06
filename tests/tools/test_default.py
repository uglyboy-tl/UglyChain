from __future__ import annotations

import http.client
import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

from uglychain.tools.default import TIMEOUT, execute_command, user_input, visit_webpage, web_search


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


@pytest.mark.parametrize(
    "input_str, expected_output",
    [
        ("Test Input", "Test Input"),
        ("Another Input", "Another Input"),
        ("", "Failed to ask user: EOF when reading a line"),
    ],
)
def test_user_input(input_str, expected_output):
    sys.stdin = StringIO(input_str)
    result = user_input(question="Test Question")
    assert result == expected_output
    sys.stdin = sys.__stdin__


@pytest.mark.parametrize(
    "query, mock_response, expected_result",
    [
        (
            "test query",
            {
                "status": 200,
                "results": [
                    {"title": "Result 1", "link": "http://example.com/1"},
                    {"title": "Result 2", "link": "http://example.com/2"},
                    {"title": "Result 3", "link": "http://example.com/3"},
                    {"title": "Result 4", "link": "http://example.com/4"},
                    {"title": "Result 5", "link": "http://example.com/5"},
                ],
            },
            "Result 1",
        ),
        ("test query", {"status": 404, "results": []}, "Failed to fetch webpage. Status code: 404"),
        ("test query", {"status": 500, "results": []}, "Failed to fetch webpage. Status code: 500"),
    ],
)
def test_web_search(monkeypatch, query, mock_response, expected_result):
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status = mock_response["status"]

            def read(self):
                return json.dumps({"results": mock_response["results"]}).encode("utf-8")

        return MockResponse()

    monkeypatch.setattr(http.client.HTTPSConnection, "request", mock_request)
    monkeypatch.setattr(http.client.HTTPSConnection, "getresponse", mock_request)

    os.environ["JINA_API_KEY"] = "test_api_key"
    result = web_search(query=query)
    if mock_response["status"] == 200:
        assert expected_result in result
    else:
        assert result == expected_result
    os.environ.pop("JINA_API_KEY")
    if mock_response["status"] == 200:
        with pytest.raises(ValueError, match="JINA_API_KEY is not set"):
            web_search(query=query)


@pytest.mark.parametrize(
    "url, mock_response, expected_content",
    [
        ("example.com", {"status": 200, "content": "Mock webpage content"}, "Mock webpage content"),
        ("another-example.com", {"status": 200, "content": "Another mock content"}, "Another mock content"),
        ("example.com", {"status": 404, "content": ""}, "Failed to fetch webpage. Status code: 404"),
    ],
)
def test_visit_webpage(monkeypatch, url, mock_response, expected_content):
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status = mock_response["status"]

            def read(self):
                return mock_response["content"].encode()

        return MockResponse()

    monkeypatch.setattr(http.client.HTTPSConnection, "request", mock_request)
    monkeypatch.setattr(http.client.HTTPSConnection, "getresponse", mock_request)

    result = visit_webpage(url=url)
    if mock_response["status"] == 200:
        assert expected_content in result
    else:
        assert result == expected_content


@pytest.mark.parametrize(
    "command, mock_response, expected_output",
    [
        (
            "echo 'Testing command output'",
            {"returncode": 0, "stdout": "Testing command output", "stderr": ""},
            "Testing command output",
        ),
        (
            "pwd",
            {"returncode": 0, "stdout": "/home/uglyboy/Code/UglyChain", "stderr": ""},
            "/home/uglyboy/Code/UglyChain",
        ),
        ("ls -la", {"returncode": 0, "stdout": "总计", "stderr": ""}, "总计"),
        ("", {"returncode": 1, "stdout": "", "stderr": ""}, "Error: Command cannot be empty."),
    ],
)
def test_execute_command(monkeypatch, command, mock_response, expected_output):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args, mock_response["returncode"], stdout=mock_response["stdout"], stderr=mock_response["stderr"]
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    result = execute_command(command=command)
    assert expected_output in result


@pytest.mark.parametrize(
    "command, mock_response, expected_output",
    [
        (
            "invalid_command",
            {"returncode": 1, "stdout": "Invalid command", "stderr": "Error"},
            "Command execution failed with return code 1",
        ),
    ],
)
def test_execute_command_with_invalid_command(monkeypatch, command, mock_response, expected_output):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args, mock_response["returncode"], stdout=mock_response["stdout"], stderr=mock_response["stderr"]
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    result = execute_command(command=command)
    assert expected_output in result
    assert mock_response["stdout"] in result
    assert mock_response["stderr"] in result


@pytest.mark.parametrize(
    "command, exception, expected_output",
    [
        ("input_error", Exception("Input error"), "Error executing command: Input error"),
        ("sleep 10", subprocess.TimeoutExpired(cmd="sleep 10", timeout=TIMEOUT), "Command execution timed out"),
        ("invalid_command", subprocess.SubprocessError("Subprocess error"), "Failed to execute command"),
        ("invalid_command", Exception("General error"), "Error executing command"),
    ],
)
def test_execute_command_with_exceptions(monkeypatch, command, exception, expected_output):
    def mock_run(*args, **kwargs):
        raise exception

    monkeypatch.setattr(subprocess, "run", mock_run)
    result = execute_command(command=command)
    assert expected_output in result
