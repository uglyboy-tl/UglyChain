from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseNode:
    completed: bool = field(init=False, default=False)
    dependencies: list[BaseNode] = field(init=False, default_factory=list)

    def add_dependency(self, node: BaseNode) -> None:
        self.dependencies.append(node)

    def __rshift__(self, other: BaseNode) -> BaseNode:
        other.add_dependency(self)
        return other

    def run(self) -> Any:
        if not all(dependency.completed for dependency in self.dependencies):
            raise ValueError("Cannot run task with uncompleted dependencies.")
        self.completed = True


def flow(task_list: list[BaseNode]) -> None:
    _deque: deque = deque(task_list)
    while _deque:
        task = _deque.pop()
        dependencies = [new_task for new_task in task.dependencies if new_task not in set(task_list)]
        _deque.extendleft(dependencies)
        task_list.extend(dependencies)

    if _has_cycle(task_list):
        raise ValueError("Circular dependency detected.")
    in_degree = {task: set(task.dependencies) for task in task_list}
    while task_list:
        current_tasks = [task for task in task_list if len(in_degree[task]) == 0 or task.completed]
        for task in current_tasks:
            if not task.completed:
                task.run()
            task_list.remove(task)

        for task in task_list:
            in_degree[task] -= set(current_tasks)


def _has_cycle(nodes: list[BaseNode]) -> bool:
    # 记录访问状态
    visited = {node: False for node in nodes}
    rec_stack = {node: False for node in nodes}

    def dfs(node: BaseNode) -> bool:
        visited[node] = True
        rec_stack[node] = True

        if not node.completed:
            for neighbor in node.dependencies:
                if not visited[neighbor]:
                    if dfs(neighbor):
                        return True
                elif rec_stack[neighbor]:
                    return True

        rec_stack[node] = False
        return False

    # 检查每个任务
    for node in nodes:
        if not visited[node]:
            if dfs(node):
                return True
    return False
