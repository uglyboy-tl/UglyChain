from __future__ import annotations

import json

import pytest
from pydantic import BaseModel, ValidationError
from src.uglychain.response_format import Mode, ResponseModel


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
        formatter.validate_response_type()


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
    result = formatter.parse_from_response(choice, use_tools=False)
    assert result.foo == "bar"  # type: ignore

    invalid_response = Choice()
    invalid_response.message.content = '{"bar": "foo"}'
    with pytest.raises(ValueError):
        formatter.parse_from_response(invalid_response)


def test_response_formatter_update_system_prompt_to_json():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    messages = [{"role": "system", "content": "Initial content"}]
    formatter.update_system_prompt_to_json(messages)
    assert "properties" in messages[0]["content"]


def test_response_formatter_update_params_to_tools():
    def mock_func() -> MockModel:
        return MockModel(foo="test")

    formatter = ResponseModel(mock_func)
    api_params = {}
    formatter.update_params_to_tools(api_params)
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
