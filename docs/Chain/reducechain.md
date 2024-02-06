# ReduceChain

> 这是一个可以串行对同类型 Prompt 进行调用的类，往往用于长文本的总结或类似处理。

## 快速使用

```python
from uglychain import MapChain

llm = ReduceChain()
input = [
    "请写出这句诗的下一句",
    "请写出这句诗的下一句",
    "请写出这句诗的下一句",
]
print(llm(input=input, history="锄禾日当午"))
```

## 高阶技巧

ReduceChain 也支持 [response_model](../Agent/structured.md) 和 [Tools](../Agent/tools.md)，通常会跟 format 参数结合使用。

```python
def string(obj: Any) -> str:
    """Converts an object to a string.

    Args:
        obj (Any): The object to be converted.
    """
    return str(obj)

tools = [string]
llm = ReduceChain(tools=tools)
input = [
    "请写出这句诗的下一句",
    "请写出这句诗的下一句",
    "请写出这句诗的下一句",
]
print(llm(input=input, history="锄禾日当午"))
```
