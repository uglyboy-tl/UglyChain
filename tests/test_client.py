from __future__ import annotations

import pytest

from uglychain.client import Client


def test_client_get(monkeypatch):
    class MockClient:
        def __init__(self):
            self.name = "MockClient"

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    client1 = Client.get()
    client2 = Client.get()

    assert client1 is client2
    assert isinstance(client1, MockClient)


def test_client_reset(monkeypatch):
    class MockClient:
        def __init__(self):
            self.name = "MockClient"

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    client1 = Client.get()
    Client.reset()
    client2 = Client.get()

    assert client1 is not client2
    assert isinstance(client2, MockClient)


def test_client_generate(monkeypatch):
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

    response = Client.generate(
        model="test:model",
        messages=[{"role": "user", "content": "Hello"}],
    )

    assert response[0].message.content == "Test response"


def test_client_generate_exception(monkeypatch):
    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    raise Exception("Test exception")

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    with pytest.raises(RuntimeError) as exc_info:
        Client.generate(
            model="test:model",
            messages=[{"role": "user", "content": "Hello"}],
        )

    assert "生成响应失败: Test exception" in str(exc_info.value)


def test_client_generate_no_choices(monkeypatch):
    class MockClient:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, messages, **kwargs):
                    return type("Response", (object,), {})

    Client.reset()
    monkeypatch.setattr("aisuite.Client", MockClient)

    with pytest.raises(ValueError) as exc_info:
        Client.generate(
            model="test:model",
            messages=[{"role": "user", "content": "Hello"}],
        )

    assert "No choices returned from the model" in str(exc_info.value)
