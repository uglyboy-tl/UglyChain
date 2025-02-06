from __future__ import annotations

import pytest
from rich.console import Console as RichConsole
from rich.live import Live
from rich.progress import Progress

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


@pytest.mark.parametrize("verbose, expected_call_count", [(True, 1), (False, 0)])
def test_log(console, mock_config, mocker, verbose, expected_call_count):
    mock_config.verbose = verbose
    mock_console = mocker.patch.object(console.console, "print")
    console.log("Test log message")
    assert mock_console.call_count == expected_call_count


@pytest.mark.parametrize("verbose, method, expected_call_count", [(True, "rule", 1), (False, "print", 0)])
def test_rule(console, mock_config, mocker, verbose, method, expected_call_count):
    mock_config.verbose = verbose
    mock_console = mocker.patch.object(console.console, method)
    console.rule("Test rule")
    assert mock_console.call_count == expected_call_count


def test_log_model_usage_pre(console, mock_config, mocker):
    mock_config.verbose = True
    mock_console = mocker.patch.object(console.console, "print")
    console.log_model_usage_pre("model", lambda x, key: key, (1,), {"key": "value"})
    mock_console.assert_called_once()


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


@pytest.mark.parametrize(
    "api_params, expected_call_count",
    [({"tools": [{"function": {"name": "test_tool", "parameters": {"param1": "value1"}}}]}, 1), ({}, 0)],
)
def test_log_api_params(console, mocker, api_params, expected_call_count):
    mock_console = mocker.patch.object(console.console, "print")
    console.log_api_params(api_params)
    assert mock_console.call_count == expected_call_count


@pytest.mark.parametrize("results", [["result1", "result2"], []])
def test_log_results(console, results):
    console.log_results(results)


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


def test_call_tool_confirm(console, mock_config, monkeypatch, mocker):
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: True)
    mock_config.need_confirm = True
    mock_console = mocker.patch.object(console.console, "print")
    result = console.call_tool_confirm("test_tool", {"param1": "value1"})
    mock_console.assert_called_once()
    assert result is True


def test_call_tool_confirm_show_info(console, mock_config, monkeypatch, mocker):
    mock_config.need_confirm = False
    mock_config.verbose = True
    console.show_react = True
    mock_console = mocker.patch.object(console.console, "print")
    console.call_tool_confirm("test_tool", {"param1": "value1"})
    mock_console.assert_called_once()


def test_pause_live(console, mocker):
    live = console._get_live()
    mock_console = mocker.patch.object(console.console, "print")
    with PauseLive(live):
        assert not live.is_started
    assert live.is_started
    mock_console.assert_called()


@pytest.mark.parametrize(
    "input, expected",
    [
        ("short", "'short'"),
        ("a very long string", "'a very l...'"),
        (12345, "12345"),
        ([1, 2, 3], "[1, 2, 3..."),
        ({"key": "value"}, "{'key':..."),
    ],
)
def test_format_arg_str(input, expected):
    assert _format_arg_str(input) == expected


@pytest.mark.parametrize(
    "args, kwargs, expected",
    [
        ((1, 2), {}, "sample_func(a=1, b=2, c=3)"),
        (
            (
                1,
                {"a": 1, "b": 2},
            ),
            {"c": 2},
            "sample_func(a=1, b={'a': 1, 'b': 2}, c=2)",
        ),
        ((1,), {"b": 2}, "sample_func(a=1, b=2, c=3)"),
        (
            (
                (1, 2, 3),
                [2, 3, 4],
                {3, 4, 5},
            ),
            {},
            "sample_func(a=(1, 2,...), b=[2, 3,...], c={3, 4,...})",
        ),
    ],
)
def test_format_func_call(args, kwargs, expected):
    def sample_func(a, b, c=3):
        return a + b + c

    assert _format_func_call(sample_func, *args, **kwargs) == expected


def test_format_func_call_with_more_than_5_args():
    def sample_func(a, b, c, d, e, f):
        return a

    assert _format_func_call(sample_func, 1, 2, 3, 4, 5, 6) == "sample_func(a=1, b=2, c=3, d=4, e=5, ...)"
