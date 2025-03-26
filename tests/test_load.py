from __future__ import annotations

from collections import namedtuple

import pytest

from uglychain.load import _parse_prompt_template, _replace_placeholder, load

Match = namedtuple("Match", ["group"])


@pytest.fixture
def prompt_file(tmp_path):
    content = """---
name: test_prompt
description: Test prompt
model: openai:test
---
system: You are a helpful assistant.
user: Hello {name}, how can I help you {today}?
"""
    file = tmp_path / "test_prompt.md"
    file.write_text(content)
    return file


def test_load_valid_file(prompt_file, mock_client):
    prompt_func = load(str(prompt_file))
    assert prompt_func.__name__ == "test_prompt"
    assert prompt_func.__doc__ == "You are a helpful assistant."
    result = prompt_func("John", today="today")
    assert result == "Test response"


@pytest.mark.parametrize(
    "invalid_content, exception, match",
    [
        ("invalid content", ValueError, "Illegal formatting of prompt file."),
        ("---\n['q','w']\n---\n", ValueError, "YAML frontmatter must be a dictionary."),
        ("---\nmodel: openai:test\n---\n{today}", TypeError, "multiple values for argument 'today'"),
    ],
)
def test_load_invalid_file(tmp_path, invalid_content, exception, match):
    invalid_file = tmp_path / "invalid.md"
    invalid_file.write_text(invalid_content)
    with pytest.raises(exception, match=match):
        func = load(str(invalid_file))
        func("a", today="today")


def test_load_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        load("nonexistent.md")


@pytest.mark.parametrize(
    "template, system, user",
    [
        ("""system: System message\nuser: User {name} template""", "System message", "User {name} template"),
        ("Test", "", "Test"),
    ],
)
def test_parse_prompt_template(template, system, user):
    _system, _user = _parse_prompt_template(template)
    assert _system == system
    assert _user == user


@pytest.mark.parametrize("invalid_content", ["a: invalid", "['q','w']"])
def test_parse_invalid_prompt_template(invalid_content):
    with pytest.raises(ValueError):
        _parse_prompt_template(invalid_content)


def test_replace_placeholder():
    match = Match(group=lambda x: "name")
    kwargs = {"name": "John"}
    result = _replace_placeholder(match, kwargs)  # type: ignore
    assert result == "John"


def test_replace_placeholder_default():
    match = Match(group=lambda x: "{name}")
    kwargs = {}
    result = _replace_placeholder(match, kwargs)  # type: ignore
    assert result == "{name}"


def test_load_with_model(prompt_file, mocker):
    mock_llm = mocker.patch("uglychain.load.llm")
    load(str(prompt_file))
    mock_llm.assert_called_once()
