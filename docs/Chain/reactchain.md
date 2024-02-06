# ReActChain

ReActChain 继承自 [LLM](llm.md)，是一个基于事件（Action）的工作流引擎，可以根据事件的结果来重新推理（Thought）并形成新的事件，最终判断任务是否完成。

所以 ReActChain 的实例化是要求必须传入一个工具列表，这个工具列表是一个工作流程的闭环，即最终可以完成任务的工具列表。当然，ReActChain 会自动在工具列表中添加一个 `finish` 工具，以便在任务完成时或者相关工具无法完成任务时，终止工作流程。

为了避免 LLM 在能力不足的情况下出现循环调用的情况，ReActChain 会约定工作流的最大长度，当工作流程的长度超过这个最大长度时，会自动终止工作流程。

其使用方式与普通的 [LLM](llm.md) 调用方式一样，但需要使用 [ReActChain](reactchain.md) 来包装工具的调用。

```python
llm = ReActChain(tools=tools)
```

但返回的结果不再是 `FunctionCall` 这个类型，而是具体的执行结果。以及如果在 ReActChain 中制定

关于 ReAct 更多的信息参见 [ReAct](../Agent/react.md)。
