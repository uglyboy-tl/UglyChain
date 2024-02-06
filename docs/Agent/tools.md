# 外部函数调用

大模型使用工具的能力是 Agent 的基本特征。在我们的库中，让所有的 LLM 均能支持外部函数调用是一个重要的目标。

当然，为了简化大模型工具的使用门槛，我们允许用户在调用时直接传入函数，而不是传入函数的名称。这样做的好处是，用户不需要在调用前导入函数，也不需要在调用前定义函数。这样的调用方式在使用上更加方便。
但这也需要用户在定义函数时，遵守一定的规范，好提供函数足够多的信息，便于大模型理解。

## 工具函数的定义

```python
class Unit(Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"


def get_current_weather(location: str, unit: Unit = Unit.FAHRENHEIT) -> str:
    """Get the current weather in a given location.

    Args:
        location (str): The city and state, e.g., San Francisco, CA
        unit (Unit): The unit to use, e.g., fahrenheit or celsius
    """
    return "Weather"


def search_baidu(query: str) -> str:
    """Search Baidu for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}是一个技术博主"


def search_google(query: str) -> str:
    """Search Google for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}是一个后端工程师"


def search_bing(query: str) -> str:
    """Search Bing for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}是一个技术博主"
```

## 外部函数调用

```python
tools = [get_current_weather]
llm = LLM(tools=tools)
print(llm("What's the weather in Beijing?"))
tools = [get_current_weather, search_baidu, search_google, search_bing]
llm = LLM(tools=tools)
print(llm("用百度查一查牛顿生于哪一年？"))
```

!!! info "工具使用的注意事项"

    在各种 Chain 中，我们都提供了 `tools` 参数，用于传入工具函数。但需要注意的是，并不是所有的 Chain 都支持外部函数调用和结构化返回的同时使用。因为这两个功能的实现是相互冲突的——结构化返回需要返回一个特定的类型，而外部函数调用则需要返回 `FunctionCall`。

    当前仅有 `ReActChain` 支持外部函数调用和结构化返回的同时使用。

### 返回结果的类型

使用函数调用功能时，我们严格要求函数的返回结果必须是一个 `FunctionCall` 类型的对象，这个对象包含了函数的名称和参数。
这样做的好处是，我们可以在调用时，无需对返回类型做任何的判断，直接将返回结果传递给模型即可。

```python
from uglychain.llm.tools import FunctionCall

class FunctionCall(BaseModel):
    name: str = Field(..., description="tool name")
    args: dict = Field(..., description="tool arguments")
```

### 返回结果的解析和使用

```python
for tool in tools:
    if tool.__name__ == response.name:
        # 使用 {tool.__name__} 工具解析
        print(tool(**response.args))
```

同时我们也提供了一个工具函数，用于解析返回结果。

```python
from uglychain.llm import run_function
def run_function (tools: List[Callable], response: FunctionCall)
```

### 如果不确定是否需要调用函数

可以引入一个直接返回结果的函数, 带来类似于 OpenAI 中 FunctionCall 的 auto 的效果。

```python
from uglychain import finish

def finish(answer: str) -> str:
    """returns the answer and finishes the task.
    Args:
        answer (str): The response to return.
    """
    return answer
```
