from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uglychain.action import Action
from uglychain.console import Console


@pytest.fixture
def console():
    console = Console()
    console.log = MagicMock()
    console._live = MagicMock()  # Initialize _live attribute
    return console


def test_obs_success(mocker, console):
    mocker.patch("uglychain.tool.Tool.call_tool", return_value="Tool output")
    action = Action(tool="mock_tool", console=console)
    assert action.obs == "Tool output"
    console.log.assert_called_with("Tool output", console.show_react, style="bold green")
    console.log.assert_called_with("Tool output", console.show_react, style="bold green")


def test_obs_exception(mocker, console):
    mocker.patch("uglychain.tool.Tool.call_tool", side_effect=Exception("Tool error"))
    action = Action(tool="mock_tool", console=console)
    assert action.obs == "Error: Tool error"
    console.log.assert_called_with("Error: Tool error", console.show_react, style="bold red")


def test_done(console):
    action = Action(tool="final_answer", console=console)
    assert action.done
    action.tool = "not_final"
    assert not action.done


def test_repr(console):
    action = Action(thought="Test thought", tool="test_tool", console=console)
    assert repr(action) == action.info


def test_info(console):
    action = Action(thought="Test thought", tool="test_tool", args={"arg1": "value1"}, console=console)
    expected_info = "\nThought: Test thought\nAction: test_tool\nAction Input: <arg1>value1</arg1>\nObservation: Error: Can't find tool test_tool"
    assert action.info == expected_info


def test_from_response(mocker, console):
    response_text = (
        "Thought: Test thought\nAction: test_tool\nAction Input: <arg1>value1</arg1>\nObservation: Tool output"
    )
    action = Action.from_response(response_text, console)
    assert action.thought.strip() == "Test thought"
    assert action.tool == "test_tool"
    assert action.args == {"arg1": "value1"}
    mocker.patch("uglychain.tool.Tool.call_tool", return_value="Tool output")
    assert action.obs == "Tool output"


def test_action_initialization(console):
    action = Action(thought="Initial thought", tool="initial_tool", args={"key": "value"}, console=console)
    assert action.thought == "Initial thought"
    assert action.tool == "initial_tool"
    assert action.args == {"key": "value"}
    assert action.console == console


def test_obs_multiple_access(mocker, console):
    mocker.patch("uglychain.tool.Tool.call_tool", return_value="Tool output")
    action = Action(tool="mock_tool", console=console)
    assert action.obs == "Tool output"
    assert action.obs == "Tool output"  # Accessing multiple times should return the same result
    console.log.assert_called_once_with("Tool output", console.show_react, style="bold green")


def test_info_various_cases(console):
    action = Action(thought="Test thought", tool="test_tool", args={"arg1": "value1"}, console=console)
    expected_info = "\nThought: Test thought\nAction: test_tool\nAction Input: <arg1>value1</arg1>\nObservation: Error: Can't find tool test_tool"
    assert action.info == expected_info

    action.tool = "final_answer"
    expected_info = "\nThought: Test thought\nAction: Finish\nObservation: Error: Can't find tool test_tool"
    assert action.info == expected_info


def test_from_response_various_inputs(console):
    response_text = (
        "Thought: Another thought\nAction: another_tool\nAction Input: <arg2>value2</arg2>\nObservation: Another output"
    )
    action = Action.from_response(response_text, console)
    assert action.thought.strip() == "Another thought"
    assert action.tool == "another_tool"
    assert action.args == {"arg2": "value2"}
    console.log.assert_called_with(" Another thought", console.show_react, style="yellow")


def test_add_special_obs_token(console):
    response_text = "Thought: Test thought\nAction: test_tool\nAction Input: <arg1>value1</arg1>"
    action = Action.from_response(response_text, console)
    assert action.thought.strip() == "Test thought"
    assert action.tool == "test_tool"
    assert action.args == {"arg1": "value1"}
    console.log.assert_called_with(" Test thought", console.show_react, style="yellow")


def test_from_response_missing_action_input(console):
    response_text = "Thought: Missing action input"
    with pytest.raises(ValueError, match="Can't parse the response, No `Action` or `Action Input`"):
        Action.from_response(response_text, console)
