from __future__ import annotations

from uglychain import Tool
from uglychain.tasks.planner import Plan, SubTask, planner


def test_subtask_initialization():
    subtask = SubTask(name="任务1", description="执行一些操作。", dependencies=["任务0"], tools=["tool1", "tool2"])
    assert subtask.name == "任务1"
    assert subtask.description == "执行一些操作。"
    assert "任务0" in subtask.dependencies
    assert "tool1" in subtask.tools
    assert "tool2" in subtask.tools


def test_plan_conversion_to_task_list(mocker):
    mock_tool1 = mocker.MagicMock(spec=Tool)
    mock_tool1.name = "tool1"
    mock_tool2 = mocker.MagicMock(spec=Tool)
    mock_tool2.name = "tool2"

    subtask1 = SubTask(name="任务1", description="执行一些操作。", dependencies=[], tools=["tool1", "tool2"])
    subtask2 = SubTask(name="任务2", description="之后的操作。", dependencies=["任务1"], tools=["tool1"])

    plan = Plan(tasks=[subtask1, subtask2])
    tasks = plan.convert_to_task_list(tools=[mock_tool1, mock_tool2])

    assert len(tasks) == 2
    assert tasks[0].description == subtask1.description
    assert tasks[1].description == subtask2.description
    assert tasks[1].dependencies[0] is tasks[0]
