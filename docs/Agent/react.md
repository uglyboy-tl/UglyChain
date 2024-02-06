# ReAct

通常的 Function Call 无法形成业务的闭环，因为 Function 的调用结果是大模型无法预知的，所以往往需要根据结果来调整对 Tools 的使用策略，以形成工作流程的闭环。

ReAct 就是为了解决这个问题而设计的，它是一个基于事件（Action）的工作流引擎，可以根据事件的结果来重新推理（Thought）并形成新的事件，最终判断任务是否完成。

## 使用方式

几乎同普通的工具调用方式一样，但需要使用 [ReActChain](../Chain/reactchain.md) 来包装工具的调用。

```python
tools = [get_current_weather]
llm = ReActChain(tools=tools)
print(llm("What's the weather in Beijing?"))
tools = [get_current_weather, search_baidu, search_google, search_bing]
llm = ReActChain(tools=tools)
print(llm("用百度查一查牛顿生于哪一年？"))
```

返回的结果不再是 `FunctionCall` 这个类型，而是具体的执行结果。
其中 ReAct 的过程会通过日志做屏幕输出，以便于理解整个工作流程。

## 部分细节

ReActChain 当前是选取自：

```python
from uglychain.chains.react_bad import ReActChain
```

这里的 `react_bad` 是因为它的实现还不够完善，需要先通过复杂的 Prompt Enginering 来实现 ReAct 流程，再通过一个匹配得到 `FunctionCall` 类型的结果。所以一步循环中会调用两次模型，效率较低。`react` 的实现可以通过一次循环就得到结果，但是目前只有 GPT4 可以在这个流程中正确使用，而其他模型可能因能力不足，导致无法正确输出 ReAct 的结果。

所以目前也使用了一个比较 trick 的方式，判断模型是否是 GPT4，如果是则 `react_bad` 中 `ReActChain` 实例化的时候会调用 `react`，否则调用 `react_bad`。

## 特别提示

ReActChain 配合 Code Interpreter 使用效果更佳，使用方法也很简单：

```python
from uglychain.tools import run_code
ReActChain(tools=[run_code])
```

这样就可以使用 Code Interpreter 了。当然，在 System Message 中给出更多的编写代码的要求，会使得使用效果更佳。

我们在 Worker 的设计中，也提供了类似方法实现的 Code Interpreter，以便于用户可以更方便的使用。
