from __future__ import annotations

import json

import pytest

from uglychain.schema import ToolResponse


def test_tool_response_parse():
    response = type("Response", (object,), {"name": "test_tool", "arguments": '{"arg1": "value1"}'})()
    tool_response = ToolResponse.parse(response)
    assert tool_response.name == "test_tool"
    assert tool_response.parameters == {"arg1": "value1"}


def test_tool_response_parse_invalid():
    response = type("Response", (object,), {"name": "test_tool", "arguments": "invalid_json"})()
    with pytest.raises(json.JSONDecodeError):
        ToolResponse.parse(response)


def test_tool_response_run_function():
    def test_tool(arg1):
        return f"arg1: {arg1}"

    tool_response = ToolResponse(name="test_tool", parameters={"arg1": "value1"})
    result = tool_response.run_function([test_tool])
    assert result == "arg1: value1"


def test_tool_response_run_function_tool_not_found():
    tool_response = ToolResponse(name="non_existent_tool", parameters={"arg1": "value1"})
    with pytest.raises(ValueError, match="Can't find tool non_existent_tool"):
        tool_response.run_function([])
