from __future__ import annotations

import pytest
from pydantic import BaseModel

from uglychain.client import Client
from uglychain.llm import _get_messages, llm


class SampleModel(BaseModel):
    content: str


def test_llm_decorator(monkeypatch):
    @llm(model="test:model")
    def sample_prompt() -> str:
        return "Hello, world!"

    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    return type(
                        "Response",
                        (object,),
                        {
                            "choices": [
                                type(
                                    "Choice",
                                    (object,),
                                    {"message": type("Message", (object,), {"content": "Test response"})},
                                )
                            ]
                        },
                    )

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_basemodel(monkeypatch):
    @llm(model="test:model")
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    return type(
                        "Response",
                        (object,),
                        {
                            "choices": [
                                type(
                                    "Choice",
                                    (object,),
                                    {
                                        "message": type(
                                            "Message", (object,), {"content": '{"content": "Test response"}'}
                                        )
                                    },
                                )
                            ]
                        },
                    )

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    result = sample_prompt()
    assert result == SampleModel(content="Test response")


def test_llm_decorator_with_list_str(monkeypatch):
    @llm(model="test:model", n=2)
    def sample_prompt() -> str:
        return "Hello, world!"

    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    return type(
                        "Response",
                        (object,),
                        {
                            "choices": [
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
                        },
                    )

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    result = sample_prompt()
    assert result == ["Test response 1", "Test response 2"]


def test_llm_decorator_with_list_basemodel(monkeypatch):
    @llm(model="test:model", n=2)  # type: ignore
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    return type(
                        "Response",
                        (object,),
                        {
                            "choices": [
                                type(
                                    "Choice",
                                    (object,),
                                    {
                                        "message": type(
                                            "Message", (object,), {"content": '{"content": "Test response 1"}'}
                                        )
                                    },
                                ),
                                type(
                                    "Choice",
                                    (object,),
                                    {
                                        "message": type(
                                            "Message", (object,), {"content": '{"content": "Test response 2"}'}
                                        )
                                    },
                                ),
                            ]
                        },
                    )

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    result = sample_prompt()
    assert result == [SampleModel(content="Test response 1"), SampleModel(content="Test response 2")]


def test_llm_decorator_without_return_annotation(monkeypatch):
    @llm(model="test:model")
    def sample_prompt():
        return "Hello, world!"

    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    return type(
                        "Response",
                        (object,),
                        {
                            "choices": [
                                type(
                                    "Choice",
                                    (object,),
                                    {"message": type("Message", (object,), {"content": "Test response"})},
                                )
                            ]
                        },
                    )

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_invalid_return_type(monkeypatch):
    @llm(model="test:model")  # type: ignore
    def sample_prompt() -> int:
        return 123  # type: ignore

    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    return type(
                        "Response",
                        (object,),
                        {
                            "choices": [
                                type(
                                    "Choice",
                                    (object,),
                                    {"message": type("Message", (object,), {"content": "Test response"})},
                                )
                            ]
                        },
                    )

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    with pytest.raises(TypeError):
        sample_prompt()


def test_llm_decorator_with_empty_api_params(monkeypatch):
    @llm(model="test:model")
    def sample_prompt():
        return "Hello, world!"

    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    return type(
                        "Response",
                        (object,),
                        {
                            "choices": [
                                type(
                                    "Choice",
                                    (object,),
                                    {"message": type("Message", (object,), {"content": "Test response"})},
                                )
                            ]
                        },
                    )

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    result = sample_prompt(api_params={})
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
