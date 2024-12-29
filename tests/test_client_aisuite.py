from __future__ import annotations

from uglychain.client_aisuite import Client


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
