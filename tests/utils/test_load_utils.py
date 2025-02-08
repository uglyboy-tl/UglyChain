from __future__ import annotations

import json

import pytest
from ruamel.yaml import YAMLError

from uglychain.utils._load_utils import (
    convert_to_variable_name,
    load_yaml,
    resolve_reference,
    resolve_references,
    update_dict_recursively,
)


@pytest.mark.parametrize(
    "origin_dict, overwrite_dict, expected",
    [
        (
            {"a": 1, "b": 2},
            {"b": 3, "c": 4},
            {"a": 1, "b": 3, "c": 4},
        ),
        (
            {"a": {"b": 1, "c": 2}},
            {"a": {"b": 3, "d": 4}},
            {"a": {"b": 3, "c": 2, "d": 4}},
        ),
        (
            {"a": 1},
            {},
            {"a": 1},
        ),
        (
            {},
            {"a": 1},
            {"a": 1},
        ),
    ],
)
def test_update_dict_recursively(origin_dict, overwrite_dict, expected):
    result = update_dict_recursively(origin_dict, overwrite_dict)
    assert result == expected


@pytest.mark.parametrize(
    "reference, expected, env_value",
    [
        ("${env:TEST_VAR}", "test_value", "test_value"),
        ("${env:NON_EXIST_VAR}", "${env:NON_EXIST_VAR}", None),
        ("normal_string", "normal_string", None),
        ("${unknown:value}", "${unknown:value}", None),
    ],
)
def test_resolve_reference_env(reference, expected, env_value, monkeypatch):
    if env_value is not None:
        monkeypatch.setenv("TEST_VAR", env_value)
    result = resolve_reference(reference)
    assert result == expected


def test_resolve_reference_file(tmp_path):
    # Test JSON file
    json_file = tmp_path / "test.json"
    json_content = {"key": "value"}
    json_file.write_text(json.dumps(json_content))

    result = resolve_reference(f"${{file:{json_file}}}")
    assert result == json_content

    # Test YAML file
    yaml_file = tmp_path / "test.yaml"
    yaml_content = "key: value\n"
    yaml_file.write_text(yaml_content)

    result = resolve_reference(f"${{file:{yaml_file}}}")
    assert result == {"key": "value"}

    # Test text file
    text_file = tmp_path / "test.txt"
    text_content = "Hello World"
    text_file.write_text(text_content)

    result = resolve_reference(f"${{file:{text_file}}}")
    assert result == text_content


def test_resolve_reference_file_not_found():
    with pytest.raises(FileNotFoundError):
        resolve_reference("${file:non_exist_file.json}")


def test_resolve_reference_with_base_path(tmp_path):
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()

    json_file = sub_dir / "test.json"
    json_content = {"key": "value"}
    json_file.write_text(json.dumps(json_content))

    result = resolve_reference("${file:test.json}", base_path=sub_dir)
    assert result == json_content


@pytest.mark.parametrize(
    "origin, expected",
    [
        (
            {"key": "${env:TEST_VAR}", "nested": {"ref": "${env:TEST_VAR}"}},
            {"key": "test_value", "nested": {"ref": "test_value"}},
        ),
        (
            ["${env:TEST_VAR}", {"key": "${env:TEST_VAR}"}],
            ["test_value", {"key": "test_value"}],
        ),
        (
            "normal_string",
            "normal_string",
        ),
        (
            123,
            123,
        ),
    ],
)
def test_resolve_references(origin, expected, monkeypatch):
    monkeypatch.setenv("TEST_VAR", "test_value")
    result = resolve_references(origin)
    assert result == expected


def test_load_yaml_none():
    assert load_yaml(None) == {}


def test_load_yaml_empty_file(tmp_path):
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.touch()
    assert load_yaml(yaml_file) == {}


def test_load_yaml_invalid_file():
    with pytest.raises(FileNotFoundError):
        load_yaml("non_exist_file.yaml")


def test_load_yaml_invalid_content(tmp_path):
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text("invalid: :")

    with pytest.raises(YAMLError):
        load_yaml(yaml_file)


def test_load_yaml_from_file(tmp_path):
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """
    key1: value1
    key2:
      nested: value2
    """
    yaml_file.write_text(yaml_content)

    result = load_yaml(yaml_file)
    assert result == {
        "key1": "value1",
        "key2": {"nested": "value2"},
    }


def test_load_yaml_from_stream(tmp_path):
    yaml_file = tmp_path / "test.yaml"
    yaml_content = "key: value\n"
    yaml_file.write_text(yaml_content)

    with yaml_file.open("r") as f:
        result = load_yaml(f)
    assert result == {"key": "value"}


def test_load_yaml_non_readable_stream(tmp_path):
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("key: value\n")

    with yaml_file.open("w") as f:
        with pytest.raises(PermissionError):
            load_yaml(f)


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("Hello World", "hello_world"),
        ("Multiple   Spaces", "multiple___spaces"),
        ("UPPERCASE", "uppercase"),
        ("already_valid_name", "already_valid_name"),
        ("", ""),
        ("Mixed Case String", "mixed_case_string"),
        ("  Leading Trailing  ", "__leading_trailing__"),
    ],
)
def test_convert_to_variable_name(input_str, expected):
    """Test convert_to_variable_name function with various input strings."""
    result = convert_to_variable_name(input_str)
    assert result == expected
