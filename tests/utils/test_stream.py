from __future__ import annotations

import threading
import time
from collections.abc import Iterator

import pytest

from uglychain.utils.stream import Stream


class TestStream:
    def test_stream_initialization(self):
        """Test that Stream initializes correctly with a source iterator."""

        # Create a source that will block until we're ready
        def blocking_source():
            event = threading.Event()
            # Block the thread until we set the event
            event.wait()
            yield "item1"
            yield "item2"
            yield "item3"

        stream = Stream(blocking_source())

        # Check that the stream has initialized correctly
        assert isinstance(stream._cache, list)
        assert stream._cache == []  # Cache should be empty since source is blocked
        assert hasattr(stream._lock, "acquire")  # Just check it has lock-like methods
        assert hasattr(stream._lock, "release")
        assert stream._stopped is False
        assert isinstance(stream._thread, threading.Thread)
        assert stream._thread.daemon is True
        assert stream._thread.is_alive() is True

    def test_stream_consumes_source(self):
        """Test that Stream consumes the source iterator and fills the cache."""
        source = iter(["item1", "item2", "item3"])
        stream = Stream(source)

        # Give the background thread time to consume the source
        time.sleep(0.1)

        # Check that the cache has been filled
        assert stream._cache == ["item1", "item2", "item3"]
        assert stream._stopped is True

    def test_stream_iterator_property(self):
        """Test that the iterator property returns a generator that yields items from the cache."""
        source = iter(["item1", "item2", "item3"])
        stream = Stream(source)

        # Give the background thread time to consume the source
        time.sleep(0.1)

        # Get an iterator from the stream
        iterator = stream.iterator

        # Check that the iterator yields the expected items
        assert next(iterator) == "item1"
        assert next(iterator) == "item2"
        assert next(iterator) == "item3"

        # Check that the iterator is exhausted
        with pytest.raises(StopIteration):
            next(iterator)

    def test_multiple_iterators(self):
        """Test that multiple iterators can be created from the same stream."""
        source = iter(["item1", "item2", "item3"])
        stream = Stream(source)

        # Give the background thread time to consume the source
        time.sleep(0.1)

        # Get two iterators from the stream
        iterator1 = stream.iterator
        iterator2 = stream.iterator

        # Check that both iterators yield the expected items
        assert list(iterator1) == ["item1", "item2", "item3"]
        assert list(iterator2) == ["item1", "item2", "item3"]

    def test_iterator_with_empty_source(self):
        """Test that the iterator works correctly with an empty source."""
        source = iter([])
        stream = Stream(source)

        # Give the background thread time to consume the source
        time.sleep(0.1)

        # Get an iterator from the stream
        iterator = stream.iterator

        # Check that the iterator is exhausted
        with pytest.raises(StopIteration):
            next(iterator)

    def test_iterator_with_slow_source(self):
        """Test that the iterator works correctly with a slow source."""

        def slow_source():
            yield "item1"
            time.sleep(0.1)
            yield "item2"
            time.sleep(0.1)
            yield "item3"

        stream = Stream(slow_source())

        # Get an iterator from the stream
        iterator = stream.iterator

        # Check that the first item is available immediately
        assert next(iterator) == "item1"

        # Wait for the second item to be produced
        time.sleep(0.15)
        assert next(iterator) == "item2"

        # Wait for the third item to be produced
        time.sleep(0.15)
        assert next(iterator) == "item3"

        # Check that the iterator is exhausted
        with pytest.raises(StopIteration):
            next(iterator)

    def test_duplicate_break_condition(self):
        """Test that the duplicate break condition in the iterator method works correctly."""
        # The Stream class has a duplicate break condition at lines 42-46
        # This test ensures that it doesn't cause any issues
        source = iter(["item1"])
        stream = Stream(source)

        # Give the background thread time to consume the source
        time.sleep(0.1)

        # Get an iterator from the stream
        iterator = stream.iterator

        # Check that the iterator yields the expected item
        assert next(iterator) == "item1"

        # Check that the iterator is exhausted
        with pytest.raises(StopIteration):
            next(iterator)

    def test_second_break_condition(self):
        """Test the second break condition in the iterator method."""
        # Since we can't directly test the duplicate code path (lines 45-46),
        # we'll note that it's a duplicate of lines 42-43 which are already covered.
        # This test is a placeholder to acknowledge the duplicate code.

        # Create a stream with an empty source
        stream = Stream(iter([]))

        # Wait for the background thread to finish
        time.sleep(0.1)

        # Verify the stream is in the expected state
        assert stream._stopped is True
        assert stream._cache == []

        # Get an iterator and verify it's empty
        iterator = stream.iterator
        with pytest.raises(StopIteration):
            next(iterator)

        # Note: The duplicate break condition at lines 45-46 is unreachable code
        # because the first identical condition at lines 42-43 will always break
        # out of the loop first. This is a code smell that should be fixed.
