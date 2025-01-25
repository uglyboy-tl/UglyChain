from __future__ import annotations

from typing import Any
from unittest.mock import ANY

import pytest
from pydantic import BaseModel

from uglychain.client import Client
from uglychain.config import config
from uglychain.llm import _gen_messages, _get_map_keys, gen_prompt, llm


class SampleModel(BaseModel):
    content: str


def create_mock_choice(content: str) -> type[Any]:
    return type("Choice", (object,), {"message": type("Message", (object,), {"content": content})})


def mock_generate(model, messages, **kwargs):
    n = 1
    if "n" in kwargs and kwargs["n"]:
        n = kwargs["n"]
    return [create_mock_choice("Test response")] * n


@pytest.fixture
def setup_client(monkeypatch):
    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)


def test_llm_decorator(setup_client):
    @llm("test:model", n=None)
    def sample_prompt() -> str:
        return "Hello, world!"

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_zero_result(monkeypatch):
    @llm
    def sample_prompt() -> str:
        return "Hello, world!"

    monkeypatch.setattr("uglychain.client.Client.generate", lambda *args, **kwargs: [])

    with pytest.raises(ValueError, match="模型未返回任何选择"):
        sample_prompt()


def test_llm_decorator_with_basemodel(monkeypatch):
    @llm(model="test:model")  # type: ignore
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    monkeypatch.setattr(
        "uglychain.client.Client.generate", lambda *args, **kwargs: [create_mock_choice('{"content": "Test response"}')]
    )

    result = sample_prompt()
    assert result == SampleModel(content="Test response")


@pytest.mark.parametrize("n", [1, 2])
def test_llm_decorator_with_list_str(setup_client, n):
    @llm(model="test:model", n=n)
    def sample_prompt() -> str:
        return "Hello, world!"

    result = sample_prompt()
    assert result == ["Test response"] * n


@pytest.mark.parametrize("n", [1, 2])
def test_llm_decorator_with_list_basemodel(monkeypatch, n):
    @llm(model="test:model", n=n)  # type: ignore
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    monkeypatch.setattr(
        "uglychain.client.Client.generate",
        lambda *args, **kwargs: [create_mock_choice('{"content": "Test response"}')] * n,
    )

    result = sample_prompt()
    assert result == [SampleModel(content="Test response")] * n


def test_llm_decorator_with_response_format(monkeypatch):
    @llm(model="test:model", response_format=SampleModel)
    def sample_prompt() -> str:
        return "Hello, world!"  # type: ignore

    monkeypatch.setattr(
        "uglychain.client.Client.generate", lambda *args, **kwargs: [create_mock_choice('{"content": "Test response"}')]
    )

    result = sample_prompt()
    assert result == SampleModel(content="Test response")


def test_llm_decorator_without_return_annotation(setup_client):
    @llm(model="test:model")
    def sample_prompt():
        return "Hello, world!"

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_need_retry(setup_client):
    @llm(model="test:model", need_retry=True)
    def sample_prompt() -> str:
        return "Hello, world!"

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_invalid_return_type(setup_client):
    @llm(model="test:model")  # type: ignore
    def sample_prompt() -> int:
        return 123  # type: ignore

    with pytest.raises(TypeError):
        sample_prompt()


def test_llm_decorator_with_empty_api_params(setup_client):
    @llm(model="test:model")
    def sample_prompt():
        return "Hello, world!"

    result = sample_prompt(api_params={})  # type: ignore
    assert result == "Test response"


def test_llm_decorator_with_inconsistent_list_lengths():
    @llm(model="test:model", map_keys=["arg1", "arg2"])
    def sample_prompt(arg1: list[str], arg2: list[str]) -> str:
        return "Hello, world!"

    with pytest.raises(ValueError, match="prompt_args 和 prompt_kwargs 中的 map_key 列表必须具有相同的长度"):
        sample_prompt(["a", "b"], ["c"])


def test_llm_decorator_with_n_and_list_length_conflict():
    @llm(model="test:model", map_keys=["arg1"], n=2)
    def sample_prompt(arg1: list[str]) -> str:
        return "Hello, world!"

    with pytest.raises(ValueError, match="n > 1 和列表长度 > 1 不能同时成立"):
        sample_prompt(["a", "b"])


def test_llm_decorator_with_parallel_processing(monkeypatch):
    @llm(model="test:model", map_keys=["arg1"])
    def sample_prompt(arg1: list[str]) -> str:
        "System prompt"
        return arg1  # type: ignore

    monkeypatch.setattr(
        "uglychain.client.Client.generate",
        lambda model, messages, **kwargs: [create_mock_choice(messages[1]["content"])],
    )

    config.use_parallel_processing = True
    results = sample_prompt(["a", "b", "c"])
    assert set(results) == {"a", "b", "c"}


def test_llm_decorator_with_tools(mocker):
    def mock_tool():
        pass

    @llm(model="test:model", tools=[mock_tool])
    def sample_prompt() -> str:
        return "Hello, world!"

    mock_generate = mocker.patch.object(Client, "generate", return_value=[create_mock_choice("Test response")])
    sample_prompt()
    mock_generate.assert_called_once_with("test:model", [{"role": "user", "content": "Hello, world!"}], tools=ANY)
    # assert result == "Test response"


def test_llm_decorator_with_invalid_tools_params(mocker):
    config.default_api_params = {"tools": "test"}

    @llm(model="test:model")
    def sample_prompt() -> str:
        return "Hello, world!"

    mock_generate = mocker.patch.object(Client, "generate", return_value=[create_mock_choice("Test response")])
    sample_prompt(api_params={"tools": "test"})  # type: ignore
    mock_generate.assert_called_once_with("test:model", [{"role": "user", "content": "Hello, world!"}])
    # assert result == "Test response"


def test_gen_messages_with_string():
    def sample_prompt():
        """System message"""
        return "User message"

    result = _gen_messages("User message", sample_prompt)
    expected = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": "User message"},
    ]
    assert result == expected


def test_gen_messages_without_docstring():
    def sample_prompt():  # type: ignore
        return "User message"

    result = _gen_messages("User message", sample_prompt)
    expected = [
        {"role": "user", "content": "User message"},
    ]
    assert result == expected

    def sample_prompt():
        return [{"role": "user", "content": "User message"}]

    result = _gen_messages([{"role": "user", "content": "User message"}], sample_prompt)
    expected = [{"role": "user", "content": "User message"}]
    assert result == expected


def test_gen_messages_with_messages_type():
    def sample_prompt():
        """System message"""
        return [{"role": "user", "content": "User message"}]

    result = _gen_messages([{"role": "user", "content": "User message"}], sample_prompt)
    expected = [{"role": "system", "content": "System message"}, {"role": "user", "content": "User message"}]
    assert result == expected


@pytest.mark.parametrize("input", [12345, [], None, "", (1), {"a": 2}])
def test_gen_messages_with_invalid_type(input):
    def sample_prompt():
        return input

    with pytest.raises(TypeError, match="Expected prompt_ret to be a str or list of Messages and not empty"):
        _gen_messages(input, sample_prompt)  # type: ignore


@pytest.mark.parametrize("map_keys", [None, []])
def test_get_map_keys_with_empty_map_keys(map_keys):
    def sample_prompt(arg1: str, arg2: str):
        return "Hello, world!"

    result = _get_map_keys(sample_prompt, ("a", "b"), {}, map_keys=map_keys)
    assert result == (1, set(), set())


def test_get_map_keys_with_different_list_lengths():
    def sample_prompt(arg1: list[str], arg2: list[str]):
        return "Hello, world!"

    with pytest.raises(ValueError, match="prompt_args 和 prompt_kwargs 中的 map_key 列表必须具有相同的长度"):
        _get_map_keys(sample_prompt, (["a", "b"], ["c"]), {}, ["arg1", "arg2"])


def test_get_map_keys_with_invalid_map_key_type():
    def sample_prompt(arg1: str):
        return "Hello, world!"

    with pytest.raises(ValueError, match="map_key 必须是列表"):
        _get_map_keys(sample_prompt, ("a",), {}, ["arg1"])


@pytest.mark.parametrize(
    "args, expected",
    [
        (("value1", "value2"), "<arg1>\nvalue1\n</arg1>\n<arg2>\nvalue2\n</arg2>"),
        ((123, ["a", "b"]), "<arg1>\n123\n</arg1>\n<arg2>\n['a', 'b']\n</arg2>"),
    ],
)
def test_gen_prompt(args, expected):
    def sample_prompt(arg1, arg2):
        return None

    result = gen_prompt(sample_prompt, *args)
    assert result == expected
