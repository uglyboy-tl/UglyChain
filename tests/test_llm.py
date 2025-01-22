from __future__ import annotations

import time
from typing import Any

import pytest
from pydantic import BaseModel

from uglychain.config import config
from uglychain.llm import _gen_messages, _get_map_keys, gen_prompt, llm, retry


class SampleModel(BaseModel):
    content: str


def create_mock_choice(content: str) -> type[Any]:
    return type("Choice", (object,), {"message": type("Message", (object,), {"content": content})})


def mock_generate(model, messages, **kwargs):
    return [create_mock_choice("Test response")]


@pytest.fixture
def setup_client(monkeypatch):
    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)


@pytest.mark.parametrize("n", [1, 2])
def test_retry_timeout(n, monkeypatch):
    def sample_function():
        time.sleep(0.2)
        return "Success"

    decorated_function = retry(n=n, timeout=0.1, wait=0)(sample_function)

    with pytest.raises(Exception, match=f"Function failed after {n} attempts"):
        decorated_function()


@pytest.mark.parametrize("n", [1, 3])
def test_retry_exception(n, monkeypatch):
    def sample_function():
        raise ValueError("Test error")

    decorated_function = retry(n=n, timeout=1, wait=0.1)(sample_function)

    with pytest.raises(Exception, match=f"Function failed after {n} attempts"):
        decorated_function()


def test_retry_success(monkeypatch):
    def sample_function():
        return "Success"

    decorated_function = retry(n=3, timeout=1, wait=1)(sample_function)

    result = decorated_function()
    assert result == "Success"


def test_llm_decorator(setup_client):
    config.default_api_params = {"tools": "test"}

    @llm("test:model", n=None)
    def sample_prompt() -> str:
        return "Hello, world!"

    @llm
    def sample1_prompt() -> str:
        return "Hello, world!"

    result = sample_prompt(api_params={"tools": "test"})  # type: ignore
    result1 = sample1_prompt()
    assert result == "Test response"
    assert result1 == "Test response"


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
def test_llm_decorator_with_list_str(monkeypatch, n):
    @llm(model="test:model", n=n)
    def sample_prompt() -> str:
        return "Hello, world!"

    monkeypatch.setattr(
        "uglychain.client.Client.generate", lambda *args, **kwargs: [create_mock_choice("Test response")] * n
    )

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


def test_llm_decorator_with_inconsistent_list_lengths(monkeypatch):
    @llm(model="test:model", map_keys=["arg1", "arg2"])
    def sample_prompt(arg1: list[str], arg2: list[str]) -> str:
        return "Hello, world!"

    with pytest.raises(ValueError, match="prompt_args 和 prompt_kwargs 中的 map_key 列表必须具有相同的长度"):
        sample_prompt(["a", "b"], ["c"])


def test_llm_decorator_with_n_and_list_length_conflict(monkeypatch):
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


def test_llm_decorator_with_tools(setup_client):
    def mock_tool():
        pass

    @llm(model="test:model", tools=[mock_tool])
    def sample_prompt() -> str:
        return "Hello, world!"

    result = sample_prompt()
    assert result == "Test response"


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
