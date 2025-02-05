from __future__ import annotations

import pytest

from uglychain.utils.xml_parse import _parse_json, parse_to_dict


def test_parse_to_dict_with_xml():
    response = "<param1>value1</param1><param2>value2</param2>"
    expected = {"param1": "value1", "param2": "value2"}
    assert parse_to_dict(response) == expected


def test_parse_to_dict_with_json(mocker):
    response = '{"param1": "value1", "param2": "value2"}'
    expected = {"param1": "value1", "param2": "value2"}
    mocker.patch("uglychain.utils.xml_parse._parse_json", return_value=expected)
    assert parse_to_dict(response) == expected


def test_parse_to_dict_with_invalid_response():
    response = "invalid response"
    with pytest.raises(ValueError, match="No parameters found in response"):
        parse_to_dict(response)


def test_parse_to_dict_with_invalid_json(mocker):
    response = '{"param1": "value1", "param2": "value2"'
    mocker.patch("uglychain.utils.xml_parse._parse_json", side_effect=ValueError("Invalid JSON format"))
    with pytest.raises(ValueError, match="No parameters found in response"):
        parse_to_dict(response)


def test_parse_json_with_valid_json():
    response = '{"param1": "value1", "param2": "value2"}'
    expected = {"param1": "value1", "param2": "value2"}
    assert _parse_json(response) == expected


def test_parse_json_with_invalid_json():
    response = '{"param1": "value1", "param2":}'
    with pytest.raises(ValueError, match="Invalid JSON format"):
        _parse_json(response)


def test_parse_json_with_no_json():
    response = "no json here"
    with pytest.raises(ValueError, match="No JSON found in response"):
        _parse_json(response)
