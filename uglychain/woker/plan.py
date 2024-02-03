import json
from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import BaseModel

from uglychain import LLM

from .base import BaseWorker

ROLE = """You are a task-generating AI known as SuperAGI.
"""

INITIALIZE_TASKS = """You are not a part of any system or device. Your role is to understand the goals presented to you, identify important components, Go through the instruction provided by the user and construct a thorough execution plan.

GOALS:
{goals}
"""

CREATE_TASKS = """
High level goal:
{goals}

You have following incomplete tasks `{pending_tasks}`. You have following completed tasks `{completed_tasks}`.

Task History:
`{task_history}`

Based on this, create a single task in plain english to be completed by your AI system ONLY IF REQUIRED to get closer to or fully reach your high level goal.
Don't create any task if it is already covered in incomplete or completed tasks.
Ensure your new task are not deviated from completing the goal.
"""

PRIORITIZE_TASKS = """
High level goal:
{goals}

You have following incomplete tasks `{pending_tasks}`. You have following completed tasks `{completed_tasks}`.

Based on this, evaluate the incomplete tasks and sort them in the order of execution. In output first task will be executed first and so on.
Remove if any tasks are unnecessary or duplicate incomplete tasks. Remove tasks if they are already covered in completed tasks.
Remove tasks if it does not help in achieving the main goal.
"""


class Tasks(BaseModel):
    tasks: List[str]


@dataclass
class Summary(BaseWorker):
    role: Optional[str] = ROLE
    prompt: str = field(init=False)
    char_limit: int = 1000
    use_reduce: bool = False
    prioritize_llm: LLM = field(init=False)

    def __post_init__(self):
        self.prioritize_llm = LLM(PRIORITIZE_TASKS, self.model, self.role)

    def run(
        self,
        goals: str,
        pending_tasks: Optional[List[str]] = None,
        completed_tasks: Optional[List[str]] = None,
        task_history: str = "",
    ):
        if pending_tasks is None:
            assert (
                completed_tasks is None and task_history == ""
            ), "Either all or none of the pending_tasks, completed_tasks and task_history should be provided"
            self.llm = LLM(INITIALIZE_TASKS, self.model, self.role, Tasks)
            kwargs = {"goals": goals}
            response = self._ask(**kwargs)
            pending_tasks = response.tasks
            completed_tasks = []
            response = self.prioritize_llm(goals=goals, pending_tasks=pending_tasks, completed_tasks=completed_tasks)
        else:
            if completed_tasks is None:
                completed_tasks = []
            self.llm = LLM(CREATE_TASKS, self.model, self.role, Tasks)
            kwargs = {
                "goals": goals,
                "pending_tasks": json.dumps(pending_tasks),
                "completed_tasks": json.dumps(completed_tasks),
                "task_history": task_history,
            }
            response = self._ask(**kwargs)
            pending_tasks.extend(response.tasks)
            response = self.prioritize_llm(goals=goals, pending_tasks=pending_tasks, completed_tasks=completed_tasks)
        if self.storage:
            self.storage.save(response.tasks)
        return response.tasks
