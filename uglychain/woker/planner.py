from dataclasses import dataclass, field
from typing import Callable, List, Optional, Union, cast

from loguru import logger
from pydantic import BaseModel, Field

from uglychain import LLM
from uglychain.tools import text_completion

from .base import BaseWorker

ROLE = "You are an expert task manager AI."

TASK_MANAGER_PROMPT = """You have to tasked with cleaning the formatting of and reprioritizing the tasks `{minified_task_list}`.

Consider the Ultimate Objective: {objective}

You need to follow these rules:
- **Do not remove any tasks**.
- Create new tasks based on the result of last task if necessary for the objective. Limit tasks types to those that can be completed with the available tools listed below. Task description should be detailed. Current tool option is {tool_names} and only.
- Do not reorder completed tasks. Only reorder and dedupe incomplete tasks.
- Make sure all task IDs are in chronological order.
- The last task is always to provide a final summary report including tasks executed and summary of knowledge acquired.

The last completed task has the following result: {result}.
"""

YOUR_FIRST_TASK = "制定一份不超过5条的任务清单"


class Task(BaseModel):
    id: int = Field(..., description="The task id.")
    task: str = Field(..., description="The task description.")
    dependent_task_ids: List[int] = Field(
        default_factory=list,
        description="The task ids that this task is dependent on. It should always be an empty array, or an array of int representing the task ID it should pull results from.",
    )


class Task_with_result(Task):
    completed: bool = True
    result: Optional[str] = Field(
        default=None, description="The task result. If the task is not completed, this field should be empty."
    )
    result_summary: Optional[str] = Field(
        default=None, description="The task result summary. If the task is not completed, this field should be empty."
    )

    @classmethod
    def from_task(cls, task: Task, result: Optional[str], result_summary: Optional[str]) -> "Task_with_result":
        return cls(
            id=task.id,
            task=task.task,
            dependent_task_ids=task.dependent_task_ids,
            result=result,
            result_summary=result_summary,
        )


class Tasks(BaseModel):
    objective: str = Field(..., description="The ultimate objective.")
    tasks: List[Task] = Field(
        ...,
        description="The list of tasks.",
    )

    @property
    def incomplete_tasks(self) -> List[Task]:
        incomplete_tasks = [task for task in self.tasks if not hasattr(task, "result")]
        incomplete_tasks.sort(key=lambda x: x.id)
        return incomplete_tasks

    @property
    def completed_tasks(self) -> List[Task]:
        completed_tasks = [task for task in self.tasks if hasattr(task, "result")]
        completed_tasks.sort(key=lambda x: x.id)
        return completed_tasks

    @property
    def tasks_completed(self) -> bool:
        return all(hasattr(task, "result") for task in self.tasks)

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    @classmethod
    def from_list(cls, objective: str, task_list: List[str]) -> "Tasks":
        tasks = [Task(id=i + 1, task=task) for i, task in enumerate(task_list)]
        return cls(objective=objective, tasks=tasks)


def execute_task(
    tasks: Tasks,
    execute: Callable[[str], str],
    summarizer_agent: Optional[Callable[[str], str]] = None,
    objective: str = "",
) -> None:
    incomplete_tasks = tasks.incomplete_tasks
    task = incomplete_tasks[0]
    if task.dependent_task_ids:
        all_dependent_tasks_complete = True
        for dep_id in task.dependent_task_ids:
            dependent_task = tasks.get_task_by_id(dep_id)
            if not dependent_task or not hasattr(dependent_task, "result"):
                all_dependent_tasks_complete = False
                break
        if not all_dependent_tasks_complete:
            logger.warning(f"Task {task.id} is dependent on other tasks.")

    if objective:
        task_prompt = f"Complete your assigned task based on the objective: {objective}. Your task: {task.task}"
    else:
        task_prompt = task.task
    result = execute(task_prompt)
    result_summary = None
    if summarizer_agent:
        result_summary = summarizer_agent(result)
    try:
        index = tasks.tasks.index(task)
        tasks.tasks[index] = Task_with_result.from_task(task, result, result_summary)
    except ValueError:
        pass  # 旧值不在列表中


@dataclass
class Planner(BaseWorker):
    role: Optional[str] = ROLE
    prompt: str = field(init=False)
    tools: List[Callable] = field(default_factory=list)
    objective: str = ""
    llm: LLM = field(init=False)

    def __post_init__(self):
        self.llm = LLM(TASK_MANAGER_PROMPT, self.model, self.role, Tasks)
        try:
            self.tools.index(text_completion)
        except ValueError:
            self.tools.insert(0, text_completion)
        self.tool_names = ", ".join([f"`{tool.__name__}`" for tool in self.tools])

    def run(
        self,
        objective: str = "",
        tasks: Optional[Union[Tasks, List[str]]] = None,
    ):
        if self.objective and objective and self.objective != objective:
            logger.warning(f"Objective has different values: {self.objective} and {objective}. use the original one.")
        elif objective:
            self.objective = objective
        assert self.objective, "Objective is required."

        if tasks is None:
            first_task = Task(id=1, task=YOUR_FIRST_TASK)
            tasks = Tasks(objective=self.objective, tasks=[first_task])
            execute_task(tasks, text_completion, objective=self.objective)
        elif isinstance(tasks, list):
            tasks = Tasks.from_list(self.objective, tasks)
            return tasks
        completed_tasks = tasks.completed_tasks
        task = cast(Task_with_result, completed_tasks[0])
        result = task.result
        original_task_list = tasks.tasks.copy()
        minified_task_list = [
            {k: v for k, v in task.model_dump().items() if k != "result" and k != "result_summary"}
            for task in tasks.tasks
        ]
        tasks = self.llm(
            objective=self.objective, minified_task_list=minified_task_list, tool_names=self.tool_names, result=result
        )
        tasks = cast(Tasks, tasks)
        if tasks.objective != self.objective:
            logger.warning(f"Objective has been changed from {self.objective} to {tasks.objective}. fix it.")
            tasks.objective = self.objective
        for i, updated_task, original_task in zip(
            range(len(original_task_list)), tasks.tasks, original_task_list, strict=False
        ):
            if updated_task.task != original_task.task:
                logger.warning(f"Task {updated_task.id} has been changed. use the new one.")
                original_task.task = updated_task.task
            if isinstance(original_task, Task_with_result):
                tasks.tasks[i] = original_task
        if self.storage:
            self.storage.save(tasks)
        return tasks
