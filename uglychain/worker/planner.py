import inspect
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Union, cast

from docstring_parser import parse
from pydantic import BaseModel, Field

from uglychain import LLM
from uglychain.tools import text_completion

from .base import BaseWorker

ROLE = "You are an expert task manager AI."

CREATE_TASKS_PROMPT = """You are an expert task list creation AI tasked with creating a list of tasks, considering the ultimate objective of your team: {objective}.
Create a very short task list based on the objective, the final output of the last task will be provided back to the user. Limit tasks types to those that can be completed with the available tools listed below. Task description should be detailed.

### AVAILABLE TOOLS: {tools_info}.

### RULES:
- The final task should always output the final result of the overall objective.
- Make sure all task IDs are in chronological order.
- Helpful Notes as guidance: "{notes}"
- no more than 5 tasks should be created.
- task descriptions should be in Chinese.
"""

TASK_MANAGER_PROMPT = """
You are a task management AI tasked with reprioritizing the a list of tasks, considering the ultimate objective of your team: {objective}. Create new tasks based on the result of last task if necessary for the objective. Limit tasks types to those that can be completed with the available tools listed below. Task description should be detailed.

### AVAILABLE TOOLS: {tools_info}.

### RULES:
- Do not remove any tasks.
- The maximum task list length is 7. Do not add an 8th task.
- Do not reorder completed tasks. Only reorder and dedupe incomplete tasks.
- Make sure all task IDs are in chronological order.
- The last step is always to provide a final summary report of all tasks.

### Here is the current task list: {tasks}
### The last completed task has the following result: {task_output}.
"""


def get_function_description(func: Callable) -> str:
    try:
        return parse(inspect.getdoc(func)).short_description  # type: ignore
    except AttributeError:
        return ""


class Task(BaseModel):
    id: int = Field(..., description="The task id.")
    task: str = Field(..., description="The task description.")
    dependent_task_ids: List[int] = Field(
        default_factory=list,
        description="The task ids that this task is dependent on. It should always be an empty array, or an array of int representing the task ID it should pull results from.",
    )
    completed: bool = Field(
        default=False,
        description="The task completion status.",
    )

    @property
    def result(self) -> str:
        if not hasattr(self, "_result"):
            self._result = ""
        return self._result

    @result.setter
    def result(self, value: str):
        self._result = value


class Tasks(BaseModel):
    tasks: List[Task] = Field(
        ...,
        description="The list of tasks.",
    )

    def get_task_by_id(self, task_id: int) -> Task:
        try:
            return next(task for task in self.tasks if task.id == task_id)
        except StopIteration as err:
            raise ValueError(f"Task with id {task_id} not found.") from err

    def execute_task(self, task: Union[Task, int], execute: Callable[[str, str, str], str], objective: str):
        if isinstance(task, int):
            task = self.get_task_by_id(task)
        assert not task.completed, f"Task {task.id} is already completed."
        dependent_tasks = [self.get_task_by_id(dependent_task_id) for dependent_task_id in task.dependent_task_ids]
        assert all(
            dependent_task.completed for dependent_task in dependent_tasks
        ), f"Dependent tasks for task {task.id} are not completed."
        dependent_task_outputs = "\n".join(dependent_task.result for dependent_task in dependent_tasks)
        result = execute(task.task, dependent_task_outputs, objective)
        task.completed = True
        task.result = result
        return result

    def reorder_tasks(self):
        self.tasks.sort(key=lambda x: x.id)

    def __str__(self):
        tasks = []
        for task in self.tasks:
            task_dict = task.model_dump()
            task_dict["completed"] = task.completed
            tasks.append(task_dict)
        return str(tasks)

    @property
    def pretty(self):
        output = "\n"
        for task in self.tasks:
            output += f"{'✓' if task.completed else '✗'} {task.id}. {task.task} [ {','.join(str(i) for i in task.dependent_task_ids)} ]\n"
        return output


@dataclass
class Planner(BaseWorker):
    role: Optional[str] = ROLE
    prompt: str = field(init=False)
    tools: List[Callable] = field(default_factory=list)
    objective: str = ""
    llm: LLM = field(init=False)

    def __post_init__(self):
        self.llm = LLM(CREATE_TASKS_PROMPT, self.model, self.role, Tasks)
        try:
            self.tools.index(text_completion)
        except ValueError:
            self.tools.insert(0, text_completion)
        self.tools_info = ", ".join([f"`{tool.__name__}`:'{get_function_description(tool)}'" for tool in self.tools])

    def run(
        self,
        objective: str = "",
        tasks: Optional[Union[Tasks, List[str]]] = None,
        task_output: str = "",
    ):
        if tasks is None or isinstance(tasks, list):
            assert not task_output, "task_output should be empty if tasks is a list."
            self.llm.prompt = CREATE_TASKS_PROMPT
            if tasks:
                notes = ";".join(f"{i+1}. {item}" for i, item in enumerate(tasks))
            else:
                notes = ""
            response = self._ask(objective=objective, tools_info=self.tools_info, notes=notes)
            return cast(Tasks, response)
        else:
            self.llm.prompt = TASK_MANAGER_PROMPT
            response = self._ask(objective=objective, tools_info=self.tools_info, task_output=task_output, tasks=tasks)
            return cast(Tasks, response)
