from __future__ import annotations

import pytest
from pydantic import BaseModel

from uglychain.llm import _get_map_keys, _get_messages, llm


class SampleModel(BaseModel):
    content: str


def test_llm_decorator(monkeypatch):
    @llm(model="test:model")
    def sample_prompt() -> str:
        return "Hello, world!"

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": "Test response"})},
            )
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_basemodel(monkeypatch):
    @llm(model="test:model")
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": '{"content": "Test response"}'})},
            )
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    result = sample_prompt()
    assert result == SampleModel(content="Test response")


def test_llm_decorator_with_list_str(monkeypatch):
    @llm(model="test:model", n=2)
    def sample_prompt() -> str:
        return "Hello, world!"

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": "Test response 1"})},
            ),
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": "Test response 2"})},
            ),
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    result = sample_prompt()
    assert result == ["Test response 1", "Test response 2"]


def test_llm_decorator_with_list_basemodel(monkeypatch):
    @llm(model="test:model", n=2)  # type: ignore
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": '{"content": "Test response 1"}'})},
            ),
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": '{"content": "Test response 2"}'})},
            ),
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    result = sample_prompt()
    assert result == [SampleModel(content="Test response 1"), SampleModel(content="Test response 2")]


def test_llm_decorator_without_return_annotation(monkeypatch):
    @llm(model="test:model")
    def sample_prompt():
        return "Hello, world!"

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": "Test response"})},
            )
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_invalid_return_type(monkeypatch):
    @llm(model="test:model")  # type: ignore
    def sample_prompt() -> int:
        return 123  # type: ignore

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": "Test response"})},
            )
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    with pytest.raises(TypeError):
        sample_prompt()


def test_llm_decorator_with_empty_api_params(monkeypatch):
    @llm(model="test:model")
    def sample_prompt():
        return "Hello, world!"

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": "Test response"})},
            )
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    result = sample_prompt(api_params={})  # type: ignore
    assert result == "Test response"


def test_get_messages_with_string():
    def sample_prompt():
        """System message"""
        return "User message"

    result = _get_messages("User message", sample_prompt)
    expected = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": "User message"},
    ]
    assert result == expected


def test_get_messages_without_docstring():
    def sample_prompt():  # type: ignore
        return "User message"

    result = _get_messages("User message", sample_prompt)
    expected = [
        {"role": "user", "content": "User message"},
    ]
    assert result == expected

    def sample_prompt():
        return [{"role": "user", "content": "User message"}]

    result = _get_messages([{"role": "user", "content": "User message"}], sample_prompt)
    expected = [{"role": "user", "content": "User message"}]
    assert result == expected


def test_get_messages_with_invalid_type():
    def sample_prompt():
        return 12345

    with pytest.raises(TypeError):
        _get_messages(12345, sample_prompt)  # type: ignore


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

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": messages[1]["content"]})},
            )
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    results = sample_prompt(["a", "b", "c"])
    assert results == ["a", "b", "c"]


def test_llm_decorator_with_tools(monkeypatch):
    def mock_tool():
        pass

    @llm(model="test:model", tools=[mock_tool])
    def sample_prompt() -> str:
        return "Hello, world!"

    def mock_generate(model, messages, **kwargs):
        assert "tools" in kwargs
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": "Test response"})},
            )
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_response_format(monkeypatch):
    @llm(model="test:model", response_format=SampleModel)
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    def mock_generate(model, messages, **kwargs):
        return [
            type(
                "Choice",
                (object,),
                {"message": type("Message", (object,), {"content": '{"content": "Test response"}'})},
            )
        ]

    monkeypatch.setattr("uglychain.client.Client.generate", mock_generate)

    result = sample_prompt()
    assert result == SampleModel(content="Test response")


def test_get_map_keys_with_empty_map_keys():
    def sample_prompt(arg1: str, arg2: str):
        return "Hello, world!"

    result = _get_map_keys(sample_prompt, ("a", "b"), {}, None)
    assert result == (1, set(), set())


def test_get_map_keys_with_invalid_map_key_type():
    def sample_prompt(arg1: str):
        return "Hello, world!"

    with pytest.raises(ValueError, match="map_key 必须是列表"):
        _get_map_keys(sample_prompt, ("a",), {}, ["arg1"])
