from __future__ import annotations

import pytest

from uglychain.react_action import Action


def mock_tool_call(mocker, mock_return):
    if isinstance(mock_return, Exception):
        mocker.patch("uglychain.tool.Tool.call_tool", side_effect=mock_return)
    else:
        mocker.patch("uglychain.tool.Tool.call_tool", return_value=mock_return)


@pytest.mark.parametrize(
    "mock_return, expected_obs, log_style, image",
    [
        ("Tool output", "Tool output", "bold green", None),
        ("Tool output\u0001image:aaa", "Tool output", "bold green", "aaa"),
        (Exception("Tool error"), "Error: Tool error", "bold red", None),
        ("Another output", "Another output", "bold green", None),
        (Exception("Another error"), "Error: Another error", "bold red", None),
    ],
)
def test_obs(mocker, console, mock_return, expected_obs, log_style, image):
    mock_tool_call(mocker, mock_return)
    action = Action(tool="mock_tool", console=console)
    assert action.obs == expected_obs
    assert action.image == image
    console.log.assert_called_with(expected_obs, console.show_react, style=log_style)


def test_done(console):
    action = Action(tool="final_answer", console=console)
    assert action.done
    action = Action(tool="not_final", console=console)
    assert not action.done


def test_repr(console):
    action = Action(thought="Test thought", tool="test_tool", console=console)
    assert repr(action) == action.info


@pytest.mark.parametrize(
    "thought, tool, args, expected_info",
    [
        (
            "Test thought",
            "test_tool",
            {"arg1": "value1"},
            "\nThought: Test thought\nAction: test_tool\nAction Input: <arg1>value1</arg1>\nObservation: Error: Can't find tool test_tool",
        ),
        (
            "Test thought",
            "final_answer",
            {},
            "\nThought: Test thought\nAction: Finish\nObservation: Error: final_answer() missing 1 required positional argument: 'answer'",
        ),
        (
            "Another thought",
            "another_tool",
            {"arg2": "value2"},
            "\nThought: Another thought\nAction: another_tool\nAction Input: <arg2>value2</arg2>\nObservation: Error: Can't find tool another_tool",
        ),
        (
            "Final thought",
            "final_tool",
            {"arg3": "value3"},
            "\nThought: Final thought\nAction: final_tool\nAction Input: <arg3>value3</arg3>\nObservation: Error: Can't find tool final_tool",
        ),
    ],
)
def test_info(console, thought, tool, args, expected_info):
    action = Action(thought=thought, tool=tool, args=args, console=console)
    assert action.info == expected_info


def test_from_response(mocker, console):
    response_text = (
        "Thought: Test thought\nAction: test_tool\nAction Input: <arg1>value1</arg1>\nObservation: Tool output"
    )
    action = Action.from_response(response_text, console)
    assert action.thought.strip() == "Test thought"
    assert action.tool == "test_tool"
    assert action.args == {"arg1": "value1"}
    mock_tool_call(mocker, "Tool output")
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


@pytest.mark.parametrize("thought, tool, args", [("", "", {}), ("a" * 100, "a" * 100, {"arg1": "a" * 100})])
def test_action_args(console, thought, tool, args):
    action = Action(thought=thought, tool=tool, args=args, console=console)
    assert action.thought == thought
    assert action.tool == tool
    assert action.args == args
    assert action.console == console


@pytest.mark.parametrize(
    "func_name, expected_name",
    [
        ("normal_name", "normal_name"),
        ("`single_backtick`", "single_backtick"),
        ("```triple_backtick```", "triple_backtick"),
        ("  spaced_name  ", "spaced_name"),
        ("```mixed`backticks```", "mixed`backticks"),
        ("```nested`backticks```", "nested`backticks"),
    ],
)
def test_fix_func_name(func_name, expected_name):
    from uglychain.react_action import _fix_func_name

    assert _fix_func_name(func_name) == expected_name


def test_from_response_with_comments(console):
    response_text = """Thought: Test with comments
Action: test_tool # this is a comment
Action Input: <arg1>value1</arg1>"""
    action = Action.from_response(response_text, console)
    assert action.tool == "test_tool"
    assert action.args == {"arg1": "value1"}


def test_format_args_multiple_params(console):
    action = Action(
        thought="Test multiple params",
        tool="test_tool",
        args={"arg1": "value1", "arg2": "value2", "arg3": "value3"},
        console=console,
    )
    expected_format = "<arg1>value1</arg1><arg2>value2</arg2><arg3>value3</arg3>"
    assert action._format_args() == expected_format


def test_short_result():
    from uglychain.react_action import _short_result

    input_data = "Line1\nLine2\nLine3\nLine4\nLine5\nLine6\nLine7\nLine8\nLine9\nLine10\nLine11\nLine12"
    expected_output = "Line1\nLine2\nLine3\nLine4\nLine5\nLine6\nLine7\nLine8\nLine9\nLine10\n..."
    assert _short_result(input_data) == expected_output

    long_text = "a" * 201
    expected_long_output = "a" * 200 + "..."
    assert _short_result(long_text) == expected_long_output

    short_text = "Short text"
    assert _short_result(short_text) == short_text
