from __future__ import annotations

import http.client
import json
import os
import sys
from io import StringIO
from pathlib import Path

import pytest

from uglychain.tools.default import execute_command, user_input, visit_webpage, web_search


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


def test_user_input():
    input_str = "Test Input"
    sys.stdin = StringIO(input_str)
    assert user_input(question="Test Question") == input_str
    sys.stdin = sys.__stdin__


def test_web_search(monkeypatch):
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status = 200

            def read(self):
                return json.dumps(
                    {
                        "results": [
                            {"title": "Result 1", "link": "http://example.com/1"},
                            {"title": "Result 2", "link": "http://example.com/2"},
                            {"title": "Result 3", "link": "http://example.com/3"},
                            {"title": "Result 4", "link": "http://example.com/4"},
                            {"title": "Result 5", "link": "http://example.com/5"},
                        ]
                    }
                ).encode("utf-8")

        return MockResponse()

    monkeypatch.setattr(http.client.HTTPSConnection, "request", mock_request)
    monkeypatch.setattr(http.client.HTTPSConnection, "getresponse", mock_request)

    os.environ["JINA_API_KEY"] = "test_api_key"
    result = web_search(query="test query")
    assert "Result 1" in result
    assert "http://example.com/1" in result
    os.environ.pop("JINA_API_KEY")
    with pytest.raises(ValueError, match="JINA_API_KEY is not set"):
        web_search(query="test query")


def test_web_search_with_wrong_response(monkeypatch):
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status = 404

            def read(self):
                return ""

        return MockResponse()

    monkeypatch.setattr(http.client.HTTPSConnection, "getresponse", mock_request)
    os.environ["JINA_API_KEY"] = "test_api_key"
    assert web_search(query="test query") == "Failed to fetch webpage. Status code: 404"


def test_visit_webpage(monkeypatch):
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status = 200

            def read(self):
                return b"Mock webpage content"

        return MockResponse()

    monkeypatch.setattr(http.client.HTTPSConnection, "request", mock_request)
    monkeypatch.setattr(http.client.HTTPSConnection, "getresponse", mock_request)

    result = visit_webpage(url="example.com")
    assert "Mock webpage content" in result


def test_visit_webpage_with_wrong_response(monkeypatch):
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status = 404

            def read(self):
                return ""

        return MockResponse()

    monkeypatch.setattr(http.client.HTTPSConnection, "getresponse", mock_request)
    assert visit_webpage(url="example.com") == "Failed to fetch webpage. Status code: 404"


@pytest.mark.parametrize(
    "arguments", [{"command": "echo 'Testing command output'"}, {"command": "pwd"}, {"command": "ls -la"}]
)
def test_execute_command(arguments):
    result = execute_command(**arguments)
    assert "Command executed successfully" in result


def test_execute_command_with_empty_command():
    with pytest.raises(ValueError, match="Command cannot be empty"):
        execute_command(command="")
