from __future__ import annotations

import logging
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from uglychain.console.simple import SimpleConsole
from uglychain.utils import Stream


@pytest.fixture
def mock_config(monkeypatch):
    """Mock the config object for testing."""

    class MockConfig:
        verbose = True
        need_confirm = False

    mock = MockConfig()
    monkeypatch.setattr("uglychain.console.simple.config", mock)
    return mock


@pytest.fixture
def mock_logger(monkeypatch):
    """Mock the logger for testing."""
    mock = MagicMock(spec=logging.Logger)
    monkeypatch.setattr("uglychain.console.simple.logger", mock)
    return mock


@pytest.fixture
def console(mock_config, mock_logger):
    """Create a SimpleConsole instance for testing."""
    return SimpleConsole("test_id")


class TestSimpleConsole:
    def test_initialization(self, console):
        """Test that SimpleConsole initializes correctly."""
        assert console.id == "test_id"
        assert console.show_base_info is True
        assert console.show_progress is True
        assert console.show_api_params is True
        assert console.show_result is True
        assert console.show_message is True
        assert console.show_react is True

    @pytest.mark.parametrize(
        "verbose, show_base_info, expected_calls",
        [
            (True, True, 3),  # All info should be logged
            (False, True, 0),  # Nothing should be logged when verbose is False
            (True, False, 0),  # Nothing should be logged when show_base_info is False
        ],
    )
    def test_base_info(self, console, mock_logger, mock_config, verbose, show_base_info, expected_calls):
        """Test the base_info method with different configurations."""
        mock_config.verbose = verbose
        console.show_base_info = show_base_info

        console.base_info(message="test_message", model="test_model")

        assert mock_logger.info.call_count == expected_calls
        if expected_calls > 0:
            mock_logger.info.assert_any_call("\nID:    test_id")
            mock_logger.info.assert_any_call("Model: test_model")
            mock_logger.info.assert_any_call("Func:  test_message")

    @pytest.mark.parametrize(
        "verbose, show_react, expected_calls",
        [
            (True, True, 1),  # Rule should be logged
            (False, True, 0),  # Nothing should be logged when verbose is False
            (True, False, 0),  # Nothing should be logged when show_react is False
        ],
    )
    def test_rule(self, console, mock_logger, mock_config, verbose, show_react, expected_calls):
        """Test the rule method with different configurations."""
        mock_config.verbose = verbose
        console.show_react = show_react

        console.rule(message="test_rule")

        assert mock_logger.info.call_count == expected_calls
        if expected_calls > 0:
            mock_logger.info.assert_called_once_with("\n--- test_rule ---")

    @pytest.mark.parametrize(
        "verbose, show_react, expected_calls",
        [
            (True, True, 1),  # Action info should be logged
            (False, True, 0),  # Nothing should be logged when verbose is False
            (True, False, 0),  # Nothing should be logged when show_react is False
        ],
    )
    def test_action_info(self, console, mock_logger, mock_config, verbose, show_react, expected_calls):
        """Test the action_info method with different configurations."""
        mock_config.verbose = verbose
        console.show_react = show_react

        console.action_info(message="test_action")

        assert mock_logger.info.call_count == expected_calls
        if expected_calls > 0:
            mock_logger.info.assert_called_once_with("test_action")

    @pytest.mark.parametrize(
        "verbose, show_react, need_confirm, message, expected_calls",
        [
            (True, True, False, "test_tool", 3),  # Tool info should be logged
            (False, True, False, "test_tool", 3),  # Tool info is always logged for regular tools
            (True, False, False, "test_tool", 3),  # Tool info should be logged even when show_react is False
            (True, True, True, "final_answer", 3),  # Should log final_answer when need_confirm is True
            (
                False,
                False,
                True,
                "final_answer",
                0,
            ),  # Should not log final_answer when verbose is False and show_react is False
        ],
    )
    def test_tool_info(
        self, console, mock_logger, mock_config, verbose, show_react, need_confirm, message, expected_calls
    ):
        """Test the tool_info method with different configurations."""
        mock_config.verbose = verbose
        mock_config.need_confirm = need_confirm
        console.show_react = show_react

        arguments = {"arg1": "value1", "arg2": "value2"}
        console.tool_info(message=message, arguments=arguments)

        assert mock_logger.info.call_count == expected_calls
        if expected_calls > 0:
            mock_logger.info.assert_any_call(f"==== {message} ====")

    def test_api_params(self, console):
        """Test the api_params method."""
        # This method doesn't do anything in SimpleConsole
        console.api_params(message={"param1": "value1"})
        console.api_params(message=None)
        # Just verify it doesn't raise any exceptions

    def test_results_with_list(self, console, mock_logger, mock_config):
        """Test the results method with a list."""
        mock_config.verbose = True
        console.show_result = True

        results = ["result1", "result2", "result3"]
        console.results(message=results)

        assert mock_logger.info.call_count == 3
        mock_logger.info.assert_any_call("result1")
        mock_logger.info.assert_any_call("result2")
        mock_logger.info.assert_any_call("result3")

    def test_results_with_none(self, console, mock_logger, mock_config):
        """Test the results method with None."""
        mock_config.verbose = True
        console.show_result = True

        console.results(message=None)

        # Should not log anything since the list is empty
        assert mock_logger.info.call_count == 0

    def test_results_not_verbose(self, console, mock_logger, mock_config):
        """Test the results method when verbose is False."""
        mock_config.verbose = False
        console.show_result = True

        results = ["result1", "result2"]
        console.results(message=results)

        # Should not log anything when verbose is False
        assert mock_logger.info.call_count == 0

    def test_results_not_show_result(self, console, mock_logger, mock_config):
        """Test the results method when show_result is False."""
        mock_config.verbose = True
        console.show_result = False

        results = ["result1", "result2"]
        console.results(message=results)

        # Should not log anything when show_result is False
        assert mock_logger.info.call_count == 0

    def test_results_with_stream(self, console, mock_config):
        """Test the results method with a Stream object."""
        mock_config.verbose = True
        console.show_result = True

        # Create a mock Stream
        mock_stream = MagicMock(spec=Stream)
        mock_stream.iterator = iter(["chunk1", "chunk2"])

        # Mock threading.Thread to capture the target function and args
        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            console.results(message=mock_stream)

            # Verify Thread was created with correct arguments
            mock_thread.assert_called_once()
            args = mock_thread.call_args[1]
            assert args["target"] == console._process_iterator
            assert args["args"] == (mock_stream.iterator,)

            # Verify thread was started and set as daemon
            assert mock_thread_instance.daemon is True
            mock_thread_instance.start.assert_called_once()

    def test_process_iterator(self, console):
        """Test the _process_iterator method."""
        # Create a test iterator
        test_iterator = iter(["chunk1", "chunk2", "chunk3"])

        # Mock print function
        with patch("builtins.print") as mock_print:
            # Call the method
            console._process_iterator(test_iterator)

            # Verify print was called for each chunk
            assert mock_print.call_count == 3
            mock_print.assert_any_call("chunk1", end="", flush=True)
            mock_print.assert_any_call("chunk2", end="", flush=True)
            mock_print.assert_any_call("chunk3", end="", flush=True)

    def test_process_iterator_with_none_chunks(self, console):
        """Test the _process_iterator method with None chunks."""
        # Create a test iterator with some None values
        test_iterator = iter(["chunk1", None, "chunk3"])

        # Mock print function
        with patch("builtins.print") as mock_print:
            # Call the method
            console._process_iterator(test_iterator)

            # Verify print was called only for non-None chunks
            assert mock_print.call_count == 2
            mock_print.assert_any_call("chunk1", end="", flush=True)
            mock_print.assert_any_call("chunk3", end="", flush=True)

    def test_process_iterator_threading(self, console):
        """Test that _process_iterator runs in a separate thread."""

        # Create a Stream with a slow iterator
        def slow_iterator():
            yield "chunk1"
            time.sleep(0.1)
            yield "chunk2"

        stream = Stream(slow_iterator())

        # Mock print function
        with patch("builtins.print") as mock_print:
            # Call results with the stream
            console.results(message=stream)

            # Give the thread time to process at least the first item
            time.sleep(0.05)

            # Verify print was called at least once
            assert mock_print.call_count >= 1
            mock_print.assert_any_call("chunk1", end="", flush=True)
