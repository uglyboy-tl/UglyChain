from __future__ import annotations

import pytest
from rich.console import Console as RichConsole
from rich.live import Live
from rich.progress import Progress

from uglychain.console import Console, PauseLive


@pytest.fixture
def mock_config(monkeypatch):
    class MockConfig:
        verbose = True
        need_confirm = True

    mock = MockConfig()
    monkeypatch.setattr("uglychain.console.config", mock)
    return mock


@pytest.fixture
def console(mock_config):
    return Console()


def test_console_initialization(console):
    assert isinstance(console.console, RichConsole)
    assert isinstance(console.progress, Progress)


@pytest.mark.parametrize("verbose, expected_call_count", [(True, 1), (False, 0)])
def test_log(console, mock_config, mocker, verbose, expected_call_count):
    mock_config.verbose = verbose
    console.show_react = True
    mock_console = mocker.patch.object(console.console, "print")
    console.action_message(message="Test log message")
    assert mock_console.call_count == expected_call_count


@pytest.mark.parametrize("verbose, method, expected_call_count", [(True, "rule", 1), (False, "print", 0)])
def test_rule(console, mock_config, mocker, verbose, method, expected_call_count):
    mock_config.verbose = verbose
    console.show_react = True
    mock_console = mocker.patch.object(console.console, method)
    console.rule(message="Test rule")
    assert mock_console.call_count == expected_call_count


def test_base_info(console, mock_config, mocker):
    mock_config.verbose = True
    mock_console = mocker.patch.object(console.console, "print")
    console.base_info(message="func", model="model")
    mock_console.assert_called_once()


def test_log_progress_methods(console):
    console.progress_start(10)
    assert hasattr(console, "_task_id")

    console.progress_intermediate()
    console.progress_end()


def test_log_messages(console):
    messages = [
        {"role": "system", "content": "test system"},
        {"role": "user", "content": "test user"},
        {"role": "assistant", "content": "test assistant"},
    ]
    console.log_messages(messages)
    assert console.messages_table.row_count == 3


@pytest.mark.parametrize(
    "api_params, expected_call_count",
    [({"tools": [{"function": {"name": "test_tool", "parameters": {"param1": "value1"}}}]}, 1), ({}, 0)],
)
def test_api_params(console, mocker, api_params, expected_call_count):
    mock_console = mocker.patch.object(console.console, "print")
    console.api_params(api_params)
    assert mock_console.call_count == expected_call_count


@pytest.mark.parametrize("results", [["result1", "result2"], []])
def test_log_results(console, results):
    console.results(results)


def test_get_live(console):
    live = console._get_live()
    assert isinstance(live, Live)
    assert live.is_started


def test_update_live(console):
    console._update_live()
    assert console._live.is_started


def test_stop_live(console):
    console._get_live()
    console._stop_live()
    assert not console._live.is_started


def test_stop_method(console):
    console._get_live()
    console.stop()
    assert not console._live.is_started


def test_call_tool_confirm(console, mock_config, monkeypatch, mocker):
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: True)
    mock_config.need_confirm = True
    result = console.call_tool_confirm("test_tool")
    assert result is True


def test_call_tool_confirm_show_info(console, mock_config, monkeypatch, mocker):
    mock_config.need_confirm = False
    mock_config.verbose = True
    console.show_react = True
    console.call_tool_confirm("test_tool")


def test_pause_live(console, mocker):
    live = console._get_live()
    mock_console = mocker.patch.object(console.console, "print")
    with PauseLive(live):
        assert not live.is_started
    assert live.is_started
    mock_console.assert_called()
