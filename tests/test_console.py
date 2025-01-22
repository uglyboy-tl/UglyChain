from __future__ import annotations

from unittest.mock import patch

import pytest
from rich.console import Console as RichConsole
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress
from rich.table import box

from uglychain.console import Console, PauseLive, _format_arg_str, _format_func_call


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


def test_init_method(console, mock_config):
    console.init()
    assert console.show_base_info == (console.show_base_info and mock_config.verbose)
    assert console.show_progress == (console.show_progress and not mock_config.verbose)
    assert console.progress.disable == (not console.show_progress)


def test_log(console, mock_config):
    mock_config.verbose = True
    with patch.object(console, "console") as mock_console:
        console.log("Test log message")
        mock_console.print.assert_called_once()
    mock_config.verbose = False
    with patch.object(console, "console") as mock_console:
        console.log("Test log message")
        mock_console.print.assert_not_called()


def test_rule(console, mock_config):
    mock_config.verbose = True
    with patch.object(console, "console") as mock_console:
        console.rule("Test rule")
        mock_console.rule.assert_called_once_with(title="Test rule")
    mock_config.verbose = False
    with patch.object(console, "console") as mock_console:
        console.rule("Test rule")
        mock_console.print.assert_not_called()


def test_log_model_usage_pre(console, mock_config):
    mock_config.verbose = True
    console.log_model_usage_pre("model", lambda x, key: key, (1,), {"key": "value"})
    # Should not raise any errors


def test_log_progress_methods(console):
    console.log_progress_start(10)
    assert hasattr(console, "_task_id")

    console.log_progress_intermediate()
    console.log_progress_end()


def test_log_messages(console):
    messages = [
        {"role": "system", "content": "test system"},
        {"role": "user", "content": "test user"},
        {"role": "assistant", "content": "test assistant"},
    ]
    console.log_messages(messages)
    assert console.messages_table.row_count == 3


def test_log_api_params(console):
    api_params = {"tools": [{"function": {"name": "test_tool", "parameters": {"param1": "value1"}}}]}
    with patch.object(console, "console") as mock_console:
        console.log_api_params(api_params)
        mock_console.print.assert_called_once()


def test_log_results(console):
    results = ["result1", "result2"]
    with patch.object(console, "console") as mock_console:
        console.log_results(results)
        mock_console.print.assert_called_once()


def test_off_method(console):
    console.off()
    assert console.show_base_info is False
    assert console.show_progress is False
    assert console.show_api_params is False
    assert console.show_result is False
    assert console.progress.disable is True


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


def test_call_tool_confirm(console, mock_config, monkeypatch):
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: True)
    mock_config.need_confirm = True
    with patch.object(console, "console") as mock_console:
        result = console.call_tool_confirm("test_tool", {"param1": "value1"})
        mock_console.print.assert_called_once()
        assert result is True
    mock_config.need_confirm = False
    mock_config.verbose = True
    console.show_react = True
    with patch.object(console, "console") as mock_console:
        console.call_tool_confirm("test_tool", {"param1": "value1"})
        mock_console.print.assert_called_once()


def test_pause_live(console):
    live = console._get_live()
    with PauseLive(live):
        assert not live.is_started
    assert live.is_started


def test_format_arg_str():
    assert _format_arg_str("short") == "'short'"
    assert _format_arg_str("a very long string") == "'a very l...'"
    assert _format_arg_str(12345) == "12345"
    assert _format_arg_str([1, 2, 3]) == "[1, 2, 3..."
    assert _format_arg_str({"key": "value"}) == "{'key':..."


def test_format_func_call():
    def sample_func(a, b, c=3):
        return a + b + c

    assert _format_func_call(sample_func, 1, 2) == "sample_func(a=1, b=2, c=3)"
    assert _format_func_call(sample_func, 1, {"a": 1, "b": 2}, c=4) == "sample_func(a=1, b={'a': 1, 'b': 2}, c=4)"
    assert _format_func_call(sample_func, 1, b=2) == "sample_func(a=1, b=2, c=3)"
    assert (
        _format_func_call(sample_func, (1, 2, 3), [2, 3, 4], {3, 4, 5})
        == "sample_func(a=(1, 2,...), b=[2, 3,...], c={3, 4,...})"
    )

    def sample1_func(a, b, c, d, e, f):
        return a

    assert _format_func_call(sample1_func, 1, 2, 3, 4, 5, 6) == "sample1_func(a=1, b=2, c=3, d=4, e=5, ...)"
