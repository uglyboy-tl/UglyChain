from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class BaseNode:
    completed: bool = field(init=False, default=False)
    dependencies: list[BaseNode] = field(init=False, default_factory=list)

    def add_dependency(self, node: BaseNode) -> None:
        self.dependencies.append(node)

    def __rshift__(self, other: BaseNode) -> BaseNode:
        other.add_dependency(self)
        return other

    def run(self) -> None:
        if not all(dependency.completed for dependency in self.dependencies):
            raise ValueError("Cannot run task with uncompleted dependencies.")
        self.completed = True


def flow(task_list: list[BaseNode]) -> None:
    _deque: deque = deque(task_list)
    while _deque:
        task = _deque.pop()
        dependencies = [task for task in task.dependencies if task not in task_list and task.completed is False]
        _deque.extendleft(dependencies)
        task_list.extend(dependencies)
        if task in _deque or len(_deque) != len(set(_deque)):
            raise ValueError("Circular dependency detected.")
    in_degree = {task: set(task.dependencies) for task in task_list}
    while task_list:
        current_tasks = [task for task in task_list if len(in_degree[task]) == 0]
        for task in current_tasks:
            task.run()
            task_list.remove(task)

        for task in task_list:
            in_degree[task] -= set(current_tasks)


if __name__ == "__main__":

    @dataclass
    class Node(BaseNode):
        name: str

        def run(self) -> None:
            super().run()
            print(self.name)

        def __hash__(self) -> int:
            return hash(self.name)

    node1 = Node("node1")
    node2 = Node("node2")
    node3 = Node("node3")
    node4 = Node("node4")
    node5 = Node("node5")

    node2 >> node4 >> node5  # type: ignore
    node1 >> node3 >> node5  # type: ignore

    flow([node5])
