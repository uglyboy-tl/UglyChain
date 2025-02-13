from __future__ import annotations

import pytest
from pydantic import BaseModel

from uglychain import config
from uglychain.structured import Mode, ResponseModel


class MockModel(BaseModel):
    foo: str


def create_mock_func() -> MockModel:
    return MockModel(foo="test")


@pytest.mark.parametrize(
    "response_type, mode",
    [
        (MockModel, Mode.MARKDOWN),
    ],
)
def test_response_formatter_init(response_type, mode):
    formatter = ResponseModel(create_mock_func)
    assert formatter.response_type == response_type
    assert formatter.mode == mode


@pytest.mark.parametrize("invalid_type", [int])
def test_response_formatter_validate_response_type(invalid_type):
    formatter = ResponseModel(create_mock_func)
    with pytest.raises(TypeError):
        formatter.response_type = invalid_type
        formatter._validate_response_type()


def test_response_formatter_get_response_format_prompt():
    formatter = ResponseModel(create_mock_func)
    prompt = formatter.parameters
    assert "properties" in prompt.keys()
    assert "foo" in str(prompt.values())


@pytest.mark.parametrize(
    "type, content, expected, exception, match",
    [
        ("json", '{"foo": "bar"}', "bar", None, None),
        (
            "json",
            '{"bar": "foo"}',
            None,
            ValueError,
            r"Failed to parse MockModel from completion \{\"bar\": \"foo\"\}\. Got: .*",
        ),
        (
            "json",
            "Invalid JSON",
            None,
            ValueError,
            "Failed to find JSON object in response for MockModel: Invalid JSON",
        ),
        ("yaml", "```yaml\nfoo: bar```", "bar", None, None),
        (
            "yaml",
            "```yaml\nbar:foo```",
            None,
            ValueError,
            r"Failed to parse MockModel from completion ```yaml\nbar:foo```. Got: .*",
        ),
        (
            "yaml",
            "Invalid YAML",
            None,
            ValueError,
            "Failed to parse MockModel from completion Invalid YAML. Got: .*",
        ),
    ],
)
def test_response_formatter_parse_from_response(type, content, expected, exception, match):
    config.response_markdown_type = type
    formatter = ResponseModel(create_mock_func)

    class Choice:
        class Message:
            def __init__(self, content: str):
                self.content = content

        def __init__(self):
            self.message = self.Message("")

    choice = Choice()
    choice.message.content = content

    if exception:
        with pytest.raises(exception, match=match):
            formatter.parse_from_response(choice)
    else:
        result = formatter.parse_from_response(choice)
        assert result.foo == expected  # type: ignore

    formatter.mode = 101  # type: ignore
    with pytest.raises(ValueError, match="Unsupported mode: 101"):
        formatter.parse_from_response(choice)


@pytest.mark.parametrize(
    "messages, exception, match",
    [
        ([{"role": "system", "content": "Initial content"}], None, None),
        ([], ValueError, "Messages is empty"),
    ],
)
def test_response_formatter_update_markdown_json_schema_from_system_prompt(messages, exception, match):
    formatter = ResponseModel(create_mock_func)
    if exception:
        with pytest.raises(exception, match=match):
            formatter._update_markdown_json_schema_from_system_prompt(messages)
    else:
        formatter._update_markdown_json_schema_from_system_prompt(messages)
        assert "properties" in messages[0]["content"]


@pytest.mark.parametrize("api_params", [({})])
def test_response_formatter_set_tools_from_params(api_params):
    formatter = ResponseModel(create_mock_func)
    formatter._set_tools_from_params(api_params)
    assert "tools" in api_params
    assert "tool_choice" in api_params


@pytest.mark.parametrize(
    "model, messages, merged_api_params", [("deepseek:test", [{"role": "system", "content": "Initial content"}], {})]
)
def test_response_formatter_process_parameters(model, messages, merged_api_params):
    formatter = ResponseModel(create_mock_func)
    formatter.process_parameters(model, messages, merged_api_params)
    assert "tools" in merged_api_params or "response_format" in merged_api_params


@pytest.mark.parametrize("api_params", [({})])
def test_response_formatter_set_response_format_from_params(api_params):
    formatter = ResponseModel(create_mock_func)
    formatter._set_response_format_from_params(api_params)
    assert "response_format" in api_params
    assert api_params["response_format"]["type"] == "json_schema"


def test_response_formatter_tool_schema():
    MockModel.__doc__ = "MockModel"
    formatter = ResponseModel(create_mock_func)
    tool_schema = formatter.tool_schema
    assert "name" in tool_schema
    assert tool_schema["name"] == "MockModel"
    assert "parameters" in tool_schema
    assert "properties" in tool_schema["parameters"]
    assert "foo" in tool_schema["parameters"]["properties"]
