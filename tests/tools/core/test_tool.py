from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uglychain.tools.core import Tool
from uglychain.tools.core.mcp import MCP


@pytest.mark.parametrize(
    "tool_name, tool_func, args, expected",
    [
        ("test_tool", MagicMock(return_value="result"), {"arg1": "value1"}, "result"),
    ],
)
def test_call_tool(tools_manager, tool_name, tool_func, args, expected):
    tools_manager.tools[tool_name] = tool_func
    result = tools_manager.call_tool(tool_name, args)
    assert result == expected
    tool_func.assert_called_once_with(**args)


def test_call_tool_with_wrong_tool_name(tools_manager):
    with pytest.raises(ValueError, match="Can't find tool non_existent_tool"):
        tools_manager.call_tool("non_existent_tool", None)


@pytest.mark.parametrize(
    "tool_name, tool_func",
    [
        ("sample_tool", lambda: None),
    ],
)
def test_register_tool(tools_manager, tool_name, tool_func):
    tools_manager.register_tool(tool_name, tool_func)
    assert tool_name in tools_manager.tools
    with pytest.raises(ValueError, match="Tool sample_tool already exists"):
        tool_func.__name__ = "sample_tool"
        Tool.tool(tool_func)
    with pytest.raises(ValueError, match="Tool sample_tool already exists"):
        tools_manager.register_tool(tool_name, tool_func)


def test_tool_call_tool(tools_manager):
    Tool._manager = tools_manager
    Tool._manager.tools["test_tool"] = MagicMock(return_value="result")
    result = Tool.call_tool("test_tool", arg1="value1")
    assert result == "result"
    tools_manager.mcp_tools.clear()


def test_tool_validate_call_tool():
    with pytest.raises(ValueError, match="Can't find tool non_existent_tool"):
        Tool.call_tool("non_existent_tool")


def test_tool_wrapper_not_implemented(monkeypatch):
    # Test the base singledispatch function raises NotImplementedError

    # Create a mock function that will be used to test the NotImplementedError
    class MockClass:
        pass

    # Import the tool_wrapper function
    from uglychain.tools.core.tool import tool_wrapper

    # We'll replace the tool_wrapper function with our mock

    # Patch the singledispatch registry to use our mock
    with monkeypatch.context() as m:
        # Create a mock implementation that raises NotImplementedError
        def mock_impl(obj, cls):
            raise NotImplementedError("Method not implemented for this type")

        # Replace the base implementation with our mock
        m.setattr("uglychain.tools.core.tool.tool_wrapper", mock_impl)

        # Now test that the NotImplementedError is raised
        with pytest.raises(NotImplementedError, match="Method not implemented for this type"):
            # This should call our mocked implementation
            from uglychain.tools.core.tool import tool_wrapper

            tool_wrapper(MockClass(), Tool)


def test_tool_mcp(tools_manager):
    # Define a test class for MCP
    class TestMCP:
        command = "test_command"
        args = ["--test"]
        env = {"TEST": "value"}

    # Set the manager
    Tool._manager = tools_manager

    # Test the mcp method
    mcp = Tool.mcp(TestMCP)

    # Verify the MCP object was created correctly
    assert isinstance(mcp, MCP)
    assert mcp.name == "TestMCP"
    assert mcp.command == "test_command"
    assert mcp.args == ["--test"]
    # The env will include PATH from the environment
    assert "TEST" in mcp.env
    assert mcp.env["TEST"] == "value"

    # Verify the MCP was registered
    assert "TestMCP" in tools_manager.mcp_names
    assert mcp.register_callback == tools_manager.register_mcp_tool


def test_load_mcp_config(tools_manager):
    # Set the manager
    Tool._manager = tools_manager

    # Clear existing MCP names to avoid conflicts
    tools_manager.mcp_names.clear()

    # Test valid config
    config_str = '"TestMCP": {"command": "test_command", "args": ["--test"], "env": {"TEST": "value"}, "disabled": false, "autoApprove": true}'
    mcp = Tool.load_mcp_config(config_str)

    # Verify the MCP object was created correctly
    assert isinstance(mcp, MCP)
    assert mcp.name == "TestMCP"
    assert mcp.command == "test_command"
    assert mcp.args == ["--test"]
    # The env will include PATH from the environment
    assert "TEST" in mcp.env
    assert mcp.env["TEST"] == "value"
    assert mcp.disabled is False
    # In the MCP class, autoApprove can be a list or a boolean
    assert mcp.autoApprove is True

    # Verify the MCP was registered
    assert "TestMCP" in tools_manager.mcp_names
    assert mcp.register_callback == tools_manager.register_mcp_tool


def test_load_mcp_config_invalid_json(tools_manager):
    # Set the manager
    Tool._manager = tools_manager

    # Test invalid JSON
    with pytest.raises(ValueError, match="Invalid JSON format"):
        Tool.load_mcp_config('"TestMCP": {invalid json}')


def test_tool_wrapper_for_class(tools_manager):
    # Set the manager
    Tool._manager = tools_manager

    # Define a test class with methods
    class TestClass:
        """Test class for tools"""

        @staticmethod
        def method1(arg1: str) -> str:
            """Test method 1"""
            return f"Method1: {arg1}"

        @staticmethod
        def method2(arg1: int, arg2: str) -> str:
            """Test method 2"""
            return f"Method2: {arg1} {arg2}"

        # Private method that should be ignored
        @staticmethod
        def _private_method():
            return "Private"

        # Non-callable attribute that should be ignored
        attribute = "test"

    # Register the class as a tool
    tools_class = Tool.tool(TestClass)

    # Verify the class was registered correctly
    assert isinstance(tools_class, type)
    assert hasattr(tools_class, "tools")
    assert len(tools_class.tools) == 2  # Only the two public methods
    assert tools_class.name == "TestClass"

    # Verify the tools were registered with the manager
    assert "TestClass:method1" in tools_manager.tools
    assert "TestClass:method2" in tools_manager.tools

    # Verify the tool objects have the correct properties
    method1_tool = next(tool for tool in tools_class.tools if tool.name == "TestClass:method1")
    assert method1_tool.description == "Test method 1"
    assert "arg1" in method1_tool.args_schema["properties"]

    method2_tool = next(tool for tool in tools_class.tools if tool.name == "TestClass:method2")
    assert method2_tool.description == "Test method 2"
    assert "arg1" in method2_tool.args_schema["properties"]
    assert "arg2" in method2_tool.args_schema["properties"]


def test_tool_wrapper_for_class_with_existing_tools(tools_manager):
    # Set the manager
    Tool._manager = tools_manager

    # Register a tool with a name that will conflict
    tools_manager.register_tool("ConflictClass:method", lambda: None)

    # Define a test class with a method that will conflict
    class ConflictClass:
        @staticmethod
        def method():
            """Conflicting method"""
            return "Method"

    # Attempt to register the class as a tool, which should raise an error
    with pytest.raises(ValueError, match="Tool ConflictClass:method already exists"):
        Tool.tool(ConflictClass)


def test_tool_wrapper_for_class_with_existing_tools_attr(tools_manager):
    # Set the manager
    Tool._manager = tools_manager

    # Define a test class with an existing tools attribute
    class TestClassWithTools:
        tools = ["existing_tool"]

        @staticmethod
        def method():
            """Test method"""
            return "Method"

    # Register the class as a tool
    tools_class = Tool.tool(TestClassWithTools)

    # Verify the existing tools attribute was replaced
    assert tools_class.tools != ["existing_tool"]
    assert len(tools_class.tools) == 1  # Only the one method
