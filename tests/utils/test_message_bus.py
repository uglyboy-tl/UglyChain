from __future__ import annotations

from uglychain.utils.message_bus import MessageBus


def test_message_bus_initialization():
    """Test that MessageBus initializes correctly."""
    bus = MessageBus("test_event", "test_module")

    assert bus.name == "test_event"
    assert bus.module == "test_module"
    assert bus.signal is not None


def test_message_bus_get_method():
    """Test that MessageBus.get() returns the same instance for the same name and module."""
    # Clear the _map to ensure a clean test
    MessageBus._map = {}

    bus1 = MessageBus.get("test_event", "test_module")
    bus2 = MessageBus.get("test_event", "test_module")

    # Should be the same instance
    assert bus1 is bus2

    # Different module should be a different instance
    bus3 = MessageBus.get("test_event", "other_module")
    assert bus1 is not bus3

    # Different name should be a different instance
    bus4 = MessageBus.get("other_event", "test_module")
    assert bus1 is not bus4
    assert bus3 is not bus4


def test_message_bus_send_with_message():
    """Test sending a message through the MessageBus."""
    # Create a MessageBus
    bus = MessageBus("test_event", "test_module")

    # Create a mock receiver function to track calls
    received_messages = []

    @bus.regedit
    def receiver(message=None, **kwargs):
        received_messages.append((message, kwargs))

    # Send a message
    bus.send("Hello, World!")

    # Check that the message was received
    assert len(received_messages) == 1
    assert received_messages[0][0] == "Hello, World!"
    assert received_messages[0][1] == {}


def test_message_bus_send_with_kwargs():
    """Test sending a message with additional kwargs through the MessageBus."""
    # Create a MessageBus
    bus = MessageBus("test_event", "test_module")

    # Create a mock receiver function to track calls
    received_messages = []

    @bus.regedit
    def receiver(message=None, **kwargs):
        received_messages.append((message, kwargs))

    # Send a message with kwargs
    bus.send(user_id=123, action="login")

    # Check that the message was received
    assert len(received_messages) == 1
    assert received_messages[0][0] is None
    assert received_messages[0][1] == {"user_id": 123, "action": "login"}


def test_message_bus_send_with_message_and_kwargs():
    """Test sending a message with additional kwargs through the MessageBus."""
    # Create a MessageBus
    bus = MessageBus("test_event", "test_module")

    # Create a mock receiver function to track calls
    received_messages = []

    @bus.regedit
    def receiver(message=None, **kwargs):
        received_messages.append((message, kwargs))

    # Send a message with kwargs
    bus.send("User logged in", user_id=123)

    # Check that the message was received
    assert len(received_messages) == 1
    assert received_messages[0][0] == "User logged in"
    assert received_messages[0][1] == {"user_id": 123}


def test_message_bus_multiple_receivers():
    """Test that multiple receivers can be registered for the same MessageBus."""
    # Create a MessageBus
    bus = MessageBus("test_event", "test_module")

    # Create mock receiver functions to track calls
    receiver1_calls = []
    receiver2_calls = []

    @bus.regedit
    def receiver1(message=None, **kwargs):
        receiver1_calls.append((message, kwargs))

    @bus.regedit
    def receiver2(message=None, **kwargs):
        receiver2_calls.append((message, kwargs))

    # Send a message
    bus.send("Test message")

    # Check that both receivers got the message
    assert len(receiver1_calls) == 1
    assert receiver1_calls[0][0] == "Test message"

    assert len(receiver2_calls) == 1
    assert receiver2_calls[0][0] == "Test message"


def test_message_bus_different_instances():
    """Test that different MessageBus instances don't interfere with each other."""
    # Create two different MessageBus instances
    bus1 = MessageBus("event1", "module1")
    bus2 = MessageBus("event2", "module2")

    # Create mock receiver functions to track calls
    receiver1_calls = []
    receiver2_calls = []

    @bus1.regedit
    def receiver1(message=None, **kwargs):
        receiver1_calls.append((message, kwargs))

    @bus2.regedit
    def receiver2(message=None, **kwargs):
        receiver2_calls.append((message, kwargs))

    # Send a message to bus1
    bus1.send("Message for bus1")

    # Check that only receiver1 got the message
    assert len(receiver1_calls) == 1
    assert receiver1_calls[0][0] == "Message for bus1"
    assert len(receiver2_calls) == 0

    # Send a message to bus2
    bus2.send("Message for bus2")

    # Check that only receiver2 got the message
    assert len(receiver1_calls) == 1  # Still just one message
    assert len(receiver2_calls) == 1
    assert receiver2_calls[0][0] == "Message for bus2"
