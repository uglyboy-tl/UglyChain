from __future__ import annotations

import pytest

from uglychain.client import Client
from uglychain.console import Console
from uglychain.session import Session


@pytest.fixture
def console(mocker):
    console = Console()
    console.action_message = mocker.MagicMock()
    console._live = mocker.MagicMock()  # Initialize _live attribute
    return console


@pytest.fixture
def session(mocker, console):
    session = Session(console=console)
    return session


@pytest.fixture
def react_session(mocker, console):
    session = Session("react", console=console)
    return session


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
