from __future__ import annotations

import pytest
from rich.console import Console as RichConsole
from rich.live import Live
from rich.progress import Progress
from rich.table import Table, box

from uglychain.console import REACT_NAME, REACT_STYLE, Console


@pytest.fixture
def mock_config(monkeypatch):
    class MockConfig:
        verbose = True

    mock = MockConfig()
    monkeypatch.setattr("uglychain.console.config", mock)
    return mock


@pytest.fixture
def console(mock_config):
    return Console()


def test_console_initialization(console):
    assert isinstance(console.console, RichConsole)
    assert isinstance(console.progress, Progress)
    assert isinstance(console.react_table, Table)
    assert console.react_table.box == box.SIMPLE
    assert console.react_table.expand is True
    assert len(console.react_table.columns) == 2


def test_init_method(console, mock_config):
    console.init()
    assert console.show_base_info == (console.show_base_info and mock_config.verbose)
    assert console.show_progress == (console.show_progress and not mock_config.verbose)
    assert console.progress.disable == (not console.show_progress)


def test_log_model_usage_pre(console, mock_config):
    mock_config.verbose = False
    console.log_model_usage_pre("model", lambda: None, (), {})
    # Should not raise any errors


def test_log_progress_methods(console):
    console.log_progress_start(10)
    assert hasattr(console, "_task_id")

    console.log_progress_intermediate()
    console.log_progress_end()


def test_log_messages(console, mock_config):
    messages = [
        {"role": "system", "content": "test system"},
        {"role": "user", "content": "test user"},
        {"role": "assistant", "content": "test assistant"},
    ]
    console.log_messages(messages)
    # Should not raise any errors


def test_log_api_params(console, mock_config):
    api_params = {"tools": [{"function": {"name": "test_tool", "parameters": {"param1": "value1"}}}]}
    console.log_api_params(api_params)
    # Should not raise any errors


def test_log_results(console, mock_config):
    results = ["result1", "result2"]
    console.log_results(results)
    # Should not raise any errors


def test_log_react(console, mock_config):
    act = {"thought": "test thought", "tool": "test tool", "args": "test args", "obs": "test obs"}
    live = Live()
    console.log_react(act, live)
    assert len(console.react_table.rows) == 4


def test_off_method(console):
    console.off()
    assert console.show_base_info is False
    assert console.show_progress is False
    assert console.show_message is False
    assert console.show_api_params is False
    assert console.show_result is False
    assert console.progress.disable is True
