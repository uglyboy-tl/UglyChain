from __future__ import annotations

import pytest

from uglychain.tasks.task import Task, TaskResponse


# Mock class for MCP and Tool
class MockTool:
    description = "Mock tool description"
    name = "mock_tool"
    args_schema = {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}


class MockMCP:
    description = "Mock MCP description"
    name = "mock_mcp"
    args_schema = {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}


# Mock TaskResponse subclass for testing
class MockTaskResponse(TaskResponse):
    pass


# Fixtures for setting up test cases
@pytest.fixture
def task_description():
    return "Sample task for testing."


@pytest.fixture
def mock_tools():
    return [MockTool(), MockMCP()]


@pytest.fixture
def task_instance(task_description, mock_tools):
    return Task(description=task_description, tools=mock_tools, reflection=True)


@pytest.fixture
def clear_class_context():
    # 清理类上下文，确保测试隔离
    yield
    if hasattr(Task, "_class_context"):
        del Task._class_context


def test_task_post_init_with_class_context(mocker, clear_class_context):
    mock_context = {"key": "value"}
    Task.set_context(mock_context)
    task_instance = Task(description="test", tools=[], reflection=False)
    assert task_instance._context == mock_context


def test_task_update_with_class_context(task_instance, mocker, clear_class_context):
    Task.set_context({})
    update_context = {"shared_key": "shared_value"}
    task_instance.update(update_context)
    assert task_instance._context["shared_key"] == "shared_value"


def test_task_run_with_reflection(task_instance, mocker):
    # Mock the _exec method to bypass actual task execution
    task_instance._reflect = mocker.Mock(return_value="Improvement suggestion")
    mock_exec = mocker.patch.object(
        task_instance, "_exec", return_value=MockTaskResponse(result="Mock result", context={})
    )
    result = task_instance.run()
    assert mock_exec.call_count == 2
    assert isinstance(result, str)
    assert task_instance["Improvement Advice"] == "Improvement suggestion"
