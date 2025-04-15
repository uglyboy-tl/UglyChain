from __future__ import annotations

import pytest

from uglychain.utils._response_parser import extract_json_dict, infer_value_type, parse_response_to_dict


@pytest.mark.parametrize(
    "response, expected",
    [
        ("<param1>value1</param1><param2>value2</param2>", {"param1": "value1", "param2": "value2"}),
        ('{"param1": "value1", "param2": "value2"}', {"param1": "value1", "param2": "value2"}),
        ("   ", {}),
        # 测试多行 XML
        (
            """
        <param1>
            value1
        </param1>
        <param2>value2</param2>
        """,
            {"param1": "\n            value1\n        ", "param2": "value2"},
        ),
        # 测试嵌套 XML 标签
        ("<outer><inner>value</inner></outer>", {"outer": "<inner>value</inner>"}),
        # 测试空 XML 标签
        ("<param1></param1><param2>value2</param2>", {"param1": "", "param2": "value2"}),
    ],
)
def test_parse_to_dict(response, expected, mocker):
    if response.startswith("{"):
        mocker.patch("uglychain.utils._response_parser.extract_json_dict", return_value=expected)
    assert parse_response_to_dict(response) == expected


@pytest.mark.parametrize(
    "response, exception, match",
    [
        ("invalid response", ValueError, "No parameters found in response"),
        ("<a>invalid response</b>", ValueError, "Invalid XML format"),
        ('{"param1": "value1", "param2": "value2"', ValueError, "No parameters found in response"),
        # 测试不匹配的 XML 标签
        ("<param1>value1</param2>", ValueError, "Invalid XML format"),
        # 测试无内容的 XML
        ("<>value</>", ValueError, "No parameters found in response"),
    ],
)
def test_parse_to_dict_exceptions(response, exception, match, mocker):
    if response.startswith("{"):
        mocker.patch(
            "uglychain.utils._response_parser.extract_json_dict", side_effect=ValueError("Invalid JSON format")
        )
    with pytest.raises(exception, match=match):
        parse_response_to_dict(response)


@pytest.mark.parametrize(
    "response, expected",
    [
        ('{"param1": "value1", "param2": "value2"}', {"param1": "value1", "param2": "value2"}),
        # 测试带有额外文本的 JSON
        ('Some text before {"param1": "value1"} and after', {"param1": "value1"}),
        # 测试多行 JSON
        (
            """
        {
            "param1": "value1",
            "param2": "value2"
        }
        """,
            {"param1": "value1", "param2": "value2"},
        ),
    ],
)
def test_parse_json(response, expected):
    assert extract_json_dict(response) == expected


@pytest.mark.parametrize(
    "response, exception, match",
    [
        ('{"param1": "value1", "param2":}', ValueError, "Invalid JSON format"),
        ("no json here", ValueError, "No JSON found in response"),
        # 测试 JSONDecodeError 情况
        ('{"key": [}', ValueError, "Invalid JSON format"),
    ],
)
def test_parse_json_exceptions(response, exception, match):
    with pytest.raises(exception, match=match):
        extract_json_dict(response)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("123", 123),  # Integer
        ("-123", -123),  # Negative integer
        ("123.45", 123.45),  # Float
        ("-123.45", -123.45),  # Negative float
        ("true", True),  # Boolean true
        ("True", True),  # Boolean True
        ("false", False),  # Boolean false
        ("False", False),  # Boolean False
        ("[1, 2, 3]", [1, 2, 3]),  # List
        ("(1, 2, 3)", (1, 2, 3)),  # Tuple
        ('{"key": "value"}', {"key": "value"}),  # Dict
        ("  123  ", 123),  # Whitespace around number
        ("  true  ", True),  # Whitespace around boolean
        ("  [1, 2, 3]  ", [1, 2, 3]),  # Whitespace around list
        ("normal string", "normal string"),  # Regular string
        ("[invalid syntax", "[invalid syntax"),  # Invalid syntax
        ("123abc", "123abc"),  # Not a valid number
    ],
)
def test_convert_value_type(value, expected):
    assert infer_value_type(value) == expected
