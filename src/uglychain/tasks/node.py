from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class BaseNode:
    dependencies: list[BaseNode] = field(init=False, default_factory=list)

    def add_dependency(self, node: BaseNode) -> None:
        self.dependencies.append(node)

    def __rshift__(self, other: BaseNode) -> BaseNode:
        other.add_dependency(self)
        return other

    def prep(self) -> list[BaseNode]:
        task_deque: list[BaseNode] = [self]
        _deque: deque = deque(task_deque)
        while _deque:
            task = _deque.pop()
            dependencies = [task for task in task.dependencies if task not in task_deque]
            _deque.extendleft(dependencies)
            task_deque.extend(dependencies)
            if task in _deque or len(_deque) != len(set(_deque)):
                raise ValueError("Circular dependency detected.")
        return task_deque

    def run(self, exec: Callable[[BaseNode], None] = lambda x: None) -> None:
        task_list = self.prep()
        in_degree = {task: set(task.dependencies) for task in task_list}
        while task_list:
            current_tasks = [task for task in task_list if len(in_degree[task]) == 0]
            for task in current_tasks:
                exec(task)
                task_list.remove(task)

            for task in task_list:
                in_degree[task] -= set(current_tasks)


@dataclass
class LogicNode(BaseNode):
    condition: Callable[..., bool]
    repeat: bool = False


if __name__ == "__main__":

    @dataclass
    class Node(BaseNode):
        name: str

        def __hash__(self) -> int:
            return hash(self.name)

    node1 = Node("node1")
    node2 = Node("node2")
    node3 = Node("node3")
    node4 = Node("node4")
    node5 = Node("node5")

    node2 >> node4 >> node5  # type: ignore
    node1 >> node3 >> node5  # type: ignore

    node5.run(lambda x: print(x.name))  # type: ignore
