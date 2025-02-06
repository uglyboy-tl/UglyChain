from __future__ import annotations

import json

import pytest

from uglychain.schema import ToolResponse


@pytest.mark.parametrize(
    "response, expected_name, expected_parameters",
    [
        (
            type("Response", (object,), {"name": "test_tool", "arguments": '{"arg1": "value1"}'})(),
            "test_tool",
            {"arg1": "value1"},
        ),
        (
            type("Response", (object,), {"name": "another_tool", "arguments": '{"arg2": "value2"}'})(),
            "another_tool",
            {"arg2": "value2"},
        ),
    ],
)
def test_tool_response_parse(response, expected_name, expected_parameters):
    tool_response = ToolResponse.parse(response)
    assert tool_response.name == expected_name
    assert tool_response.parameters == expected_parameters


@pytest.mark.parametrize(
    "response",
    [
        type("Response", (object,), {"name": "test_tool", "arguments": "invalid_json"})(),
        type("Response", (object,), {"name": "another_tool", "arguments": "not_a_json"})(),
    ],
)
def test_tool_response_parse_invalid(response):
    with pytest.raises(json.JSONDecodeError):
        ToolResponse.parse(response)


@pytest.mark.parametrize(
    "tool_response, tools, expected_result",
    [
        (ToolResponse(name="test_tool", parameters={"arg1": "value1"}), [lambda arg1: f"arg1: {arg1}"], "arg1: value1"),
        (
            ToolResponse(name="another_tool", parameters={"arg2": "value2"}),
            [lambda arg2: f"arg2: {arg2}"],
            "arg2: value2",
        ),
    ],
)
def test_tool_response_run_function(tool_response, tools, expected_result):
    tools[0].__name__ = tool_response.name

    result = tool_response.run_function(tools)
    assert result == expected_result


@pytest.mark.parametrize(
    "tool_response, tools, expected_exception, match",
    [
        (
            ToolResponse(name="non_existent_tool", parameters={"arg1": "value1"}),
            [],
            ValueError,
            "Can't find tool non_existent_tool",
        ),
        (
            ToolResponse(name="another_non_existent_tool", parameters={"arg2": "value2"}),
            [],
            ValueError,
            "Can't find tool another_non_existent_tool",
        ),
    ],
)
def test_tool_response_run_function_tool_not_found(tool_response, tools, expected_exception, match):
    with pytest.raises(expected_exception, match=match):
        tool_response.run_function(tools)
