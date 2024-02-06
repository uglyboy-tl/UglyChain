# 信息检索

让模型可以利用外部的信息库来帮助回答问题，是一种常见且有效的增强模型能力的方法。而这种方法对于具体场景的特定任务的完成更是尤为重要。

但需要注意的是，信息检索的效果往往取决于信息库的质量和多样性。因此，我们需要在实际应用中，根据具体的场景和任务，选择或搭建合适的信息库。

所以在我们的框架中，没有默认提供很多信息库，而是提供了一种通用的接口，让用户可以方便的接入自己的信息库。

## 信息检索的接口

我们提供了一个通用的信息检索接口，用户可以通过实现这个接口，来接入自己的信息库。

```python
class BaseRetriever(ABC):
    default_n: int = DEFAULT_N

    @abstractmethod
    def search(self, query: str, n: int) -> List[str]:
        pass

    def get(self, query: str) -> str:
        try:
            return self.search(query, 1)[0]
        except Exception:
            return ""


@dataclass
class StoresRetriever(BaseRetriever, ABC):
    path: str
    start_init: bool = False

    def __post_init__(self):
        if self.start_init:
            self.init()
        else:
            self._load()

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def add(self, text: str, metadata: Optional[Dict[str, str]] = None):
        pass

    def _load(self):
        self.init()

    def all(self) -> List[str]:
        return []
```

其中，`StoresRetriever` 是一个定制化的信息检索接口，它提供了一些额外的方法，用于信息库的初始化、添加和获取所有信息的操作。

## 提供的信息检索实现

### BingRetriever

`BingRetriever` 是一个使用 Bing 搜索引擎的信息检索实现。它需要用户提供 Bing 的 API key。

### ArxivRetriever

`ArxivRetriever` 是一个使用 arXiv 的信息检索实现。它可以根据用户提供的关键词，返回 arXiv 上的论文摘要。

### LlamaIndexRetriever[未验证]

`LlamaIndexRetriever` 是一个使用 LlamaIndex 的信息检索实现。它可以让用于连接到自己的 LlamaIndex 接口，从而实现信息检索。而其他信息索引的建立等操作，可以通过 LlamaIndex 中大家更熟悉的方式来完成。关于 LlamaIndex 的更多信息，可以参考 [这里](https://docs.llamaindex.ai/en/stable/)。

### BM25Retriever

`BM25Retriever` 是一个使用 BM25 算法的信息检索实现。它可以根据用户提供的文档，建立索引，并根据用户提供的查询，返回最相关的文档。
它主要提供了一种简单的本地化信息检索的方式。对于一些 Worker 功能的实现（例如需要查询相关的历史信息，或者寻找最适合的 Samples 等），可以在不引入外部信息库的情况下，依旧能保证功能正常运行。

### DBRetriever[未实现]

`DBRetriever` 是一个使用数据库的信息检索实现。它可以根据用户提供的数据库，返回相关的信息。

它核心的远离是利用 LLM 将用户的 query 转换为 SQL 语句，然后再利用数据库的查询能力，返回相关的信息。

### CombineRetrievers[未实现]

`CombineRetrievers` 是一个将多个信息检索实现组合在一起的信息检索实现。

但这个模块最重要的能力不是合并多个信息检索的结果，而是利用 LLM 的能力，智能的生成适合的 query，然后再利用多个信息检索的结果，来生成最契合用户需求的结果。
