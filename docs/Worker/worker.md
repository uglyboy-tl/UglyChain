# 工作节点

在更加复杂的实际应用中，对大模型的使用场景往往是高度具体和重复性的，所以我们将类似的具体使用场景下的操作封装成一个个的工作节点，以便于复用和维护。

每个工作节点外部并不需要理解更具体的模型参数或实现流程，只需要知道具体工作节点的实际功能和输入输出即可。这样可以大大降低使用者的使用门槛，提高使用效率。

## 常见的需要大模型能力的工作节点

一些常见功能的工作节点我们都进行了封装，具体节点如下：

- [分类节点](classify.md)
- [摘要节点](summary.md)
- [Code Interpreter 节点](ci.md)
- [任务规划节点](plan.md)

另外还有一些更直接的使用模型能力的工作节点，如：

- 写代码节点
- 代码优化节点
- 角色扮演节点
- RAG 问答节点
- 翻译节点
- 续写节点
- ...

类似的节点基本上都可以通过修改 Prompt 来实现，我们对之没有进行进一步的封装，但在 Example 中给出了部分例子。用户可以根据自己的需求进行封装使用。

## 工作节点的结构

```python
@dataclass
class BaseWorker(ABC):
    role: Optional[str] = None
    prompt: str = "{prompt}"
    model: Model = Model.DEFAULT
    retriever: Optional[BaseRetriever] = None
    storage: Optional[Storage] = None
```

工作节点的结构如上所示，其中包含了工作节点的基本属性，如角色设定、输入模板、模型选择等。用户可以根据自己的需求进行修改。

### [Retriever](../Agent/retriever.md)

retriever 是一个可选的属性，用于在工作节点中使用检索器。检索器可以帮助工作节点更好地理解用户的输入，提高工作节点的效果。
通常我们都会使用 retriever 来实现 RAG 的功能。

可以根据实际场景的不同来引入特定的检索器，如在 Code Interpreter 节点中使用 CodeRetriever 来检索代码片段，或在 RAG 问答节点中使用 RAGRetriever 来检索相关的文档，或通常都可以在工作节点中使用 WebSearchRetriever 来检索网络上的相关信息。

### Storage[未实现]

storage 是一个可选的属性，用于在工作节点中使用存储器。存储器可以帮助工作节点持久化的保存节点的执行结果，便于其他节点更好的使用（例如出错后重启流程）当前节点的结果，而不必总是重复执行大模型的调用流程（太慢）。
