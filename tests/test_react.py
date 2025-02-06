from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uglychain.client import Client
from uglychain.react import final_answer, react
from uglychain.schema import ToolResponse
from uglychain.tool import Tool


@pytest.fixture
def mock_tool():
    tool = MagicMock(spec=Tool)
    tool.name = "mock_tool"
    tool.description = "A mock tool for testing."
    tool.args_schema = {}
    return tool


@pytest.fixture
def mock_prompt():
    def prompt(*args, **kwargs):
        return "Test prompt"

    return prompt


def test_final_answer():
    assert final_answer(answer="Test Answer") == "Test Answer"


def test_react_basic(mock_tool, mock_prompt, mocker):
    mocker.patch.object(
        Client,
        "generate",
        return_value=[
            type(
                "Choice",
                (object,),
                {
                    "message": type(
                        "Message",
                        (object,),
                        {"content": "Thought: aaa\nAction: final_answer\nAction Input: <answer>Test Answer</answer>"},
                    )
                },
            )
        ],
    )
    decorated_func = react(tools=[mock_tool])(mock_prompt)
    result = decorated_func()
    assert result == "Test Answer"
