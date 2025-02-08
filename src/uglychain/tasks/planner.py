from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from uglychain import Tool, llm
from uglychain.tasks.task import Task


class SubTask(BaseModel):
    name: str = Field(description="The name of the task. Output in Chinese")
    description: str = Field(description="The task to be performed. Output in Chinese")
    dependencies: list[str] = Field(
        description="The name of tasks that must be completed before this task can be performed."
    )
    tools: list[str] = Field(description="Tools that may be used to perform this task, at least two for user choice.")


class Plan(BaseModel):
    """
    This plan should involve individual tasks based on the available tools, that if executed correctly will yield the correct answer.
    Do not skip steps, do not add any superfluous steps. Only write the high-level plan, DO NOT DETAIL INDIVIDUAL TOOL CALLS.
    """

    tasks: list[SubTask] = Field(description="The tasks to be performed. Output in Chinese")

    def convert_to_task_list(self, tools: list[Tool]) -> list[Task]:
        tools_dict = {tool.name: tool for tool in tools}
        share_context: dict[str, Any] = {}
        Task.set_context(share_context)

        def generate_task(task: SubTask) -> Task:
            return Task(
                description=task.description,
                tools=[tools_dict[tool_name] for tool_name in task.tools],
            )

        tasks_dict = {task.name: generate_task(task) for task in self.tasks}
        for task in self.tasks:
            for dep in task.dependencies:
                tasks_dict[task.name].dependencies.append(tasks_dict[dep])
        return [tasks_dict[task.name] for task in self.tasks]


@llm(response_format=Plan)
def planner(objective: str, tool_descriptions: str) -> str:
    """You are a world expert at making efficient plans to solve any task using a set of carefully crafted tools.
    Now for the given objective, develop a step-by-step high-level plan taking into account the above inputs."""
    return f"""Here is your objective:

Objective:
```
{objective}
```

Your plan can leverage any of these tools:
{tool_descriptions}

Now begin! Write your plan below."""
