from __future__ import annotations

import pytest

from uglychain.utils._parse import _parse_json, parse_to_dict


@pytest.mark.parametrize(
    "response, expected",
    [
        ("<param1>value1</param1><param2>value2</param2>", {"param1": "value1", "param2": "value2"}),
        ('{"param1": "value1", "param2": "value2"}', {"param1": "value1", "param2": "value2"}),
        ("   ", {}),
    ],
)
def test_parse_to_dict(response, expected, mocker):
    if response.startswith("{"):
        mocker.patch("uglychain.utils._parse._parse_json", return_value=expected)
    assert parse_to_dict(response) == expected


@pytest.mark.parametrize(
    "response, exception, match",
    [
        ("invalid response", ValueError, "No parameters found in response"),
        ('{"param1": "value1", "param2": "value2"', ValueError, "No parameters found in response"),
    ],
)
def test_parse_to_dict_exceptions(response, exception, match, mocker):
    if response.startswith("{"):
        mocker.patch("uglychain.utils._parse._parse_json", side_effect=ValueError("Invalid JSON format"))
    with pytest.raises(exception, match=match):
        parse_to_dict(response)


@pytest.mark.parametrize(
    "response, expected", [('{"param1": "value1", "param2": "value2"}', {"param1": "value1", "param2": "value2"})]
)
def test_parse_json(response, expected):
    assert _parse_json(response) == expected


@pytest.mark.parametrize(
    "response, exception, match",
    [
        ('{"param1": "value1", "param2":}', ValueError, "Invalid JSON format"),
        ("no json here", ValueError, "No JSON found in response"),
    ],
)
def test_parse_json_exceptions(response, exception, match):
    with pytest.raises(exception, match=match):
        _parse_json(response)
