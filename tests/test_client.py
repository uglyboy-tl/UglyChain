from __future__ import annotations

import os

import pytest

from uglychain.client import Client, _router


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
        assert isinstance(response, list)
        assert response[0].message.content == expected_response


@pytest.mark.parametrize(
    "api_params,messages,expected_response,exception",
    [
        (
            {"stream": True},
            [{"role": "user", "content": "Hello"}],
            [type("Choice", (object,), {"message": type("Message", (object,), {"content": "Test response"})})],
            None,
        ),
        (
            {},
            [{"role": "user", "content": "Hello"}],
            None,
            RuntimeError("生成响应失败: No choices returned from the model"),
        ),
        (
            {"stream": False},
            [{"role": "user", "content": "Hello"}],
            [type("Choice", (object,), {"message": type("Message", (object,), {"content": "Test response"})})],
            None,
        ),
        ({}, None, None, RuntimeError("生成响应失败: Messages must be provided")),
    ],
)
def test_client_generate_extended(monkeypatch, mock_client, api_params, messages, expected_response, exception):
    model = "test:model"
    if exception:

        class MockClientWithException(mock_client):
            class chat:  # noqa: N801
                class completions:  # noqa: N801
                    @staticmethod
                    def create(model, messages, **kwargs):
                        if expected_response is not None:
                            return type("Response", (object,), {"choices": expected_response})
                        else:
                            raise exception

        Client.reset()
        monkeypatch.setattr("aisuite.Client", MockClientWithException)

        with pytest.raises(type(exception)) as exc_info:
            Client.generate(model=model, messages=messages, **api_params)
        assert str(exception) in str(exc_info.value)
    else:
        response = Client.generate(model=model, messages=messages, **api_params)
        assert isinstance(response, list)
        assert response[0].message.content == expected_response[0].message.content


def test_router_openrouter(mock_client, mocker):
    mock_client.configure = mocker.MagicMock()
    model = "openrouter:model_name"
    expected_model = "openai:model_name"

    # Mock环境变量
    os.environ["OPENROUTER_API_KEY"] = "test_key"

    result = _router(model, mock_client)
    assert result == expected_model
    mock_client.configure.assert_called_once_with(
        {"openai": {"api_key": "test_key", "base_url": "https://openrouter.ai/api/v1"}}
    )


def test_router_other(mock_client):
    model = "provider:model_name"
    result = _router(model, mock_client)
    assert result == model
