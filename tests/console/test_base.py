from __future__ import annotations

import pytest

from uglychain.console.base import EmptyConsole
from uglychain.schema import Messages
from uglychain.utils import Stream


@pytest.fixture
def empty_console():
    """Create an EmptyConsole instance for testing."""
    return EmptyConsole("test_id")


class TestEmptyConsole:
    def test_initialization(self, empty_console):
        """Test that EmptyConsole initializes correctly."""
        assert empty_console.id == "test_id"
        assert empty_console.show_base_info is True
        assert empty_console.show_progress is True
        assert empty_console.show_api_params is True
        assert empty_console.show_result is True
        assert empty_console.show_message is True
        assert empty_console.show_react is True

    def test_base_info(self, empty_console):
        """Test the base_info method."""
        # Should not raise any exceptions
        empty_console.base_info(message="test_message", model="test_model")

    def test_rule(self, empty_console):
        """Test the rule method."""
        # Should not raise any exceptions
        empty_console.rule(message="test_rule")

    def test_action_info(self, empty_console):
        """Test the action_info method."""
        # Should not raise any exceptions
        empty_console.action_info(message="test_action")

    def test_tool_info(self, empty_console):
        """Test the tool_info method."""
        # Should not raise any exceptions
        empty_console.tool_info(message="test_tool", arguments={"arg1": "value1"})

    def test_api_params(self, empty_console):
        """Test the api_params method."""
        # Should not raise any exceptions
        empty_console.api_params(message={"param1": "value1"})
        empty_console.api_params(message=None)

    def test_results(self, empty_console):
        """Test the results method."""
        # Should not raise any exceptions
        empty_console.results(message=["result1", "result2"])
        empty_console.results(message=None)

        # Test with Stream
        mock_stream = Stream(iter(["chunk1", "chunk2"]))
        empty_console.results(message=mock_stream)

    def test_progress_methods(self, empty_console):
        """Test the progress methods."""
        # Should not raise any exceptions
        empty_console.progress_start(10)
        empty_console.progress_intermediate()
        empty_console.progress_end()

    def test_messages(self, empty_console):
        """Test the messages method."""
        # Should not raise any exceptions
        test_messages = Messages(
            [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}]
        )
        empty_console.messages(test_messages)

    def test_call_tool_confirm(self, empty_console):
        """Test the call_tool_confirm method."""
        # Should always return True
        result = empty_console.call_tool_confirm("test_tool")
        assert result is True
