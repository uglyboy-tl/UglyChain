from __future__ import annotations

import pytest

from uglychain.client import Client


@pytest.fixture
def mock_client(monkeypatch):
    class MockClient:
        def __init__(self):
            self.name = "MockClient"

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
    return MockClient


@pytest.mark.parametrize("reset", [False, True])
def test_client_get_and_reset(mock_client, reset):
    client1 = Client.get()
    if reset:
        Client.reset()
    client2 = Client.get()

    if reset:
        assert client1 is not client2
    else:
        assert client1 is client2
    assert isinstance(client2, mock_client)


@pytest.mark.parametrize(
    "expected_response,exception",
    [
        ("Test response", None),
        (None, RuntimeError("生成响应失败: Test exception")),
        (type("Response", (object,), {}), ValueError("No choices returned from the model")),
    ],
)
def test_client_generate(monkeypatch, mock_client, expected_response, exception):
    model = "test:model"
    messages = [{"role": "user", "content": "Hello"}]
    if exception:

        class MockClientWithException(mock_client):
            class chat:  # noqa: N801
                class completions:  # noqa: N801
                    @staticmethod
                    def create(model, messages, **kwargs):
                        if expected_response:
                            return expected_response
                        else:
                            raise Exception("Test exception")

        Client.reset()
        monkeypatch.setattr("aisuite.Client", MockClientWithException)

        with pytest.raises(type(exception)) as exc_info:
            Client.generate(model=model, messages=messages)
        assert str(exception) in str(exc_info.value)
    else:
        response = Client.generate(model=model, messages=messages)
        assert response[0].message.content == expected_response
