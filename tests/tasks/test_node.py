from __future__ import annotations

from dataclasses import dataclass

import pytest

from uglychain.tasks.node import BaseNode, flow


@dataclass
class Node(BaseNode):
    name: str

    def __hash__(self) -> int:
        return hash(self.name)


@pytest.mark.parametrize(
    "node1_name, node2_name, node3_name, completed, circular, exception, match",
    [
        ("node1", "node2", None, False, False, ValueError, "Cannot run task with uncompleted dependencies."),
        ("node1", "node2", None, True, False, None, None),
        ("node1", "node2", "node3", False, False, None, None),
        ("node1", "node2", "node3", True, False, None, None),
        ("node1", "node2", "node3", True, True, None, None),
        ("node1", "node2", "node3", False, True, ValueError, "Circular dependency detected."),
    ],
)
def test_node_operations(node1_name, node2_name, node3_name, completed, exception, match, circular):
    node1 = Node(node1_name)
    node2 = Node(node2_name)
    node1.completed = completed
    node1 >> node2  # type: ignore
    if node3_name:
        node3 = Node(node3_name)
        node2 >> node3  # type: ignore
        task_list: list[BaseNode] = [node3]
        if circular:
            node3 >> node1  # type: ignore
        if exception:
            with pytest.raises(exception, match=match):
                flow(task_list)
        else:
            flow(task_list)
            assert node1.completed
            assert node2.completed
            assert node3.completed
    else:
        if exception:
            with pytest.raises(exception, match=match):
                node2.run()
        else:
            node2.run()
            assert node2.completed


def test_flow_circular_dependency():
    node1 = Node("node1")
    node2 = Node("node2")
    node3 = Node("node3")
    node1 >> node2 >> node3 >> node1  # type: ignore
    task_list: list[BaseNode] = [node1, node2]
    with pytest.raises(ValueError, match="Circular dependency detected."):
        flow(task_list)
