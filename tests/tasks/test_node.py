from __future__ import annotations

from dataclasses import dataclass

import pytest

from uglychain.tasks.node import BaseNode, flow


@dataclass
class Node(BaseNode):
    name: str

    def __hash__(self) -> int:
        return hash(self.name)


def test_add_dependency():
    node1 = Node("node1")
    node2 = Node("node2")
    node1.add_dependency(node2)
    assert node2 in node1.dependencies


def test_rshift_operator():
    node1 = Node("node1")
    node2 = Node("node2")
    node1 >> node2  # type: ignore
    assert node1 in node2.dependencies


def test_run_without_dependencies():
    node = Node("node")
    node.run()
    assert node.completed


def test_run_with_uncompleted_dependencies():
    node1 = Node("node1")
    node2 = Node("node2")
    node1 >> node2  # type: ignore
    with pytest.raises(ValueError, match="Cannot run task with uncompleted dependencies."):
        node2.run()


def test_run_with_completed_dependencies(mocker):
    node1 = Node("node1")
    node2 = Node("node2")
    node1.completed = True
    node1 >> node2  # type: ignore
    node2.run()
    assert node2.completed


def test_flow_normal_execution(mocker):
    node1 = Node("node1")
    node2 = Node("node2")
    node3 = Node("node3")
    node1 >> node2 >> node3  # type: ignore
    task_list: list[BaseNode] = [node3, node2, node1]
    flow(task_list)
    assert node1.completed
    assert node2.completed
    assert node3.completed


def test_flow_circular_dependency():
    node1 = Node("node1")
    node2 = Node("node2")
    node3 = Node("node3")
    node1 >> node2 >> node3 >> node1  # type: ignore
    task_list: list[BaseNode] = [node1, node2]
    print(node1)
    with pytest.raises(ValueError, match="Circular dependency detected."):
        flow(task_list)
