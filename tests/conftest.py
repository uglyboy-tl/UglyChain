from __future__ import annotations

import pytest

from uglychain.client import Client
from uglychain.console import EmptyConsole
from uglychain.session import Session
from uglychain.tools.core.tool_manager import ToolsManager


@pytest.fixture
def console(mocker):
    console = EmptyConsole("test")
    console.action_info = mocker.MagicMock()
    return console


@pytest.fixture
def session(mocker, console):
    session = Session()
    session.console_register(console)
    return session


@pytest.fixture
def react_session(mocker, console):
    session = Session("react")
    session.console_register(console)
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


@pytest.fixture
def tools_manager():
    tools_manager = ToolsManager()
    tools_manager.mcp_tools.clear()
    return tools_manager
