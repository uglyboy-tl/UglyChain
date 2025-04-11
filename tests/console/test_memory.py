from __future__ import annotations

from uglychain.console.memory import Memory
from uglychain.schema import Messages


def test_memory_initialization():
    """Test that Memory console can be initialized."""
    memory_console = Memory(id="test")
    assert memory_console is not None
    assert isinstance(memory_console, Memory)
    assert hasattr(memory_console, "memory")
    assert isinstance(memory_console.memory, dict)


def test_memory_messages_storage():
    """Test that messages are stored in memory."""
    # Clear the class variable before test
    Memory.memory = {}

    memory_console = Memory(id="test")
    test_id = memory_console.id

    # Create test messages
    test_messages = Messages(
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there! How can I help you today?"},
        ]
    )

    # Store messages
    memory_console.messages(test_messages)

    # Verify messages are stored
    assert test_id in Memory.memory
    assert len(Memory.memory[test_id]) == 1
    assert Memory.memory[test_id][0] == test_messages


def test_multiple_messages_storage():
    """Test that multiple messages are stored correctly."""
    # Clear the class variable before test
    Memory.memory = {}

    memory_console = Memory(id="test")
    test_id = memory_console.id

    # Create test messages
    test_messages1 = Messages(
        [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}]
    )

    test_messages2 = Messages(
        [
            {"role": "assistant", "content": "Hi there! How can I help you today?"},
            {"role": "user", "content": "What's the weather like?"},
        ]
    )

    # Store messages
    memory_console.messages(test_messages1)
    memory_console.messages(test_messages2)

    # Verify messages are stored
    assert test_id in Memory.memory
    assert len(Memory.memory[test_id]) == 2
    assert Memory.memory[test_id][0] == test_messages1
    assert Memory.memory[test_id][1] == test_messages2


def test_multiple_console_instances():
    """Test that multiple console instances store messages separately."""
    # Clear the class variable before test
    Memory.memory = {}

    memory_console1 = Memory(id="test1")
    memory_console2 = Memory(id="test2")

    test_id1 = memory_console1.id
    test_id2 = memory_console2.id

    # Create test messages
    test_messages1 = Messages(
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello from console 1!"},
        ]
    )

    test_messages2 = Messages(
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello from console 2!"},
        ]
    )

    # Store messages
    memory_console1.messages(test_messages1)
    memory_console2.messages(test_messages2)

    # Verify messages are stored separately
    assert test_id1 in Memory.memory
    assert test_id2 in Memory.memory
    assert len(Memory.memory[test_id1]) == 1
    assert len(Memory.memory[test_id2]) == 1
    assert Memory.memory[test_id1][0] == test_messages1
    assert Memory.memory[test_id2][0] == test_messages2
