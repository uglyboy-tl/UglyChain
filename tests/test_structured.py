from __future__ import annotations

import re

import pytest
from pydantic import BaseModel

from uglychain.structured import Mode, ResponseModel


class MockModel(BaseModel):
    foo: str


def test_response_formatter_init():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)

    assert formatter.response_type == MockModel
    assert formatter.mode == Mode.MD_JSON


def test_response_formatter_validate_response_type():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    with pytest.raises(TypeError):
        formatter.response_type = int
        formatter._validate_response_type()


def test_response_formatter_get_response_format_prompt():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    prompt = formatter.parameters
    assert "properties" in prompt.keys()
    assert "foo" in str(prompt.values())


def test_response_formatter_parse_from_response():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)

    class Choice:
        class Message:
            def __init__(self, content: str):
                self.content = content

        def __init__(self):
            self.message = self.Message("")

    choice = Choice()
    choice.message.content = '{"foo": "bar"}'
    result = formatter.parse_from_response(choice)
    assert result.foo == "bar"  # type: ignore

    invalid_response = Choice()
    invalid_response.message.content = '{"bar": "foo"}'
    with pytest.raises(
        ValueError, match=re.compile(r"Failed to parse MockModel from completion \{\"bar\": \"foo\"\}\. Got: .*")
    ):
        formatter.parse_from_response(invalid_response)

    response = Choice()
    response.message.content = "Invalid JSON"
    with pytest.raises(ValueError, match="Failed to find JSON object in response for MockModel: Invalid JSON"):
        formatter.parse_from_response(response)

    formatter.mode = 101  # type: ignore
    with pytest.raises(ValueError, match="Unsupported mode: 101"):
        formatter.parse_from_response(choice)


def test_response_formatter_update_markdown_json_schema_from_system_prompt():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    messages = [{"role": "system", "content": "Initial content"}]
    formatter._update_markdown_json_schema_from_system_prompt(messages)
    assert "properties" in messages[0]["content"]


def test_response_formatter_set_tools_from_params():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    api_params = {}
    formatter._set_tools_from_params(api_params)
    assert "tools" in api_params
    assert "tool_choice" in api_params


def test_response_formatter_process_parameters():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    messages = [{"role": "system", "content": "Initial content"}]
    merged_api_params = {}
    formatter.process_parameters("openai:gpt-4o", messages, merged_api_params)
    assert "tools" in merged_api_params or "response_format" in merged_api_params


def test_response_formatter_set_response_format_from_params():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    api_params = {}
    formatter._set_response_format_from_params(api_params)
    assert "response_format" in api_params
    assert api_params["response_format"]["type"] == "json_schema"


def test_response_formatter_schema():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    schema = formatter.schema
    assert "properties" in schema
    assert "foo" in schema["properties"]


def test_response_formatter_openai_schema():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    MockModel.__doc__ = "MockModel"
    formatter = ResponseModel(mock_func)
    openai_schema = formatter.openai_schema
    assert "name" in openai_schema
    assert openai_schema["name"] == "MockModel"
    assert "parameters" in openai_schema
    assert "properties" in openai_schema["parameters"]
    assert "foo" in openai_schema["parameters"]["properties"]


def test_update_markdown_json_schema_from_system_prompt():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    with pytest.raises(ValueError, match="Messages is empty"):
        formatter._update_markdown_json_schema_from_system_prompt([])
