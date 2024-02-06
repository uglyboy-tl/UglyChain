# 任务规划节点

一些具体执行时有复杂细节的任务，通过 [Tools](../Agent/tools.md) 或者 [Code Interpreter](ci.md) 来执行是很难取得良好效果的。

这些任务更适合通过提前规划，将任务分解成多个节点，然后再具体执行。而这就是任务规划节点的作用。

Planner 的实现参考了 [BabyAGI](https://github.com/yoheinakajima/babyagi) 的实现

## 任务规划节点的使用

```python
worker = Planner(tools=tools)
worker.run(objective=objective)
```

其中 `tools` 是我们解决这个问题能使用的工具。`objective` 是我们要解决的具体问题。

这里我们默认会向 `tools` 中添加一个名为 `text_completion` 的工具，作用是调用大模型自身能力来回答问题。这样在一些纯文本的问题中，我们可以直接使用大模型自身的能力来解决问题。

````python

## 任务规划节点的返回结果的格式
```python
class Task(BaseModel):
    id: int
    task: str
    dependent_task_ids: List[int]
    completed

class Tasks(BaseModel):
    tasks: List[Task]
````

## 任务规划节点的优化

通常的问题，我们可以通过任务规划节点生成的任务列表，根据其中提到的依赖关系，设计并行的流程来执行程序。

但类似于在 [ReAct](../Agent/react.md) 中提到的，面对 [Tools](../Agent/tools.md) 返回结果的不确定性，往往我们还需要在任务执行的过程中，动态的调整规划好的任务列表。

我们可以在获得了任务执行结果后，将任务执行结果传递给任务规划节点，让任务规划节点根据任务执行结果，动态的调整任务列表。

```python
tasks = worker.run(tasks=tasks, task_output=task_output)
```

## 任务执行的具体命令

为了便于任务列表 `Tasks` 更新自身的信息，我们也约定了任务执行的具体命令的格式。

```python
task_output = tasks.execute_task(task, execute, objective)
```

其中 `task` 是任务列表中的一个任务，`objective` 是任务的目标，而 `execute` 是一个待实现的函数，用于接收全部的上下文信息，再根据具体的工具来执行任务。
