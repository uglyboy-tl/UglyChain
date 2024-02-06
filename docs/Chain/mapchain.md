# MapChain

> 这是一个可以并行对同类型 Prompt 进行调用的类，可以大大提高调用效率。

## 快速使用

```python
from uglychain import MapChain

llm = MapChain()
print(llm([
        {"input": "How old are you?"},
        {"input": "What is the meaning of life?"},
        {"input": "What is the hottest day of the year?"},
    ]))
```

## 高阶技巧

可以使用 `prompt_template` 来对 Prompt 进行参数化，使用 [response_model](../Agent/structured.md) 来对返回结果进行结构化。

```python
class AUTHOR(BaseModel):
    name: str = Field(..., description="姓名")
    introduction: str = Field(..., description="简介")

llm = MapChain(prompt_template="{book}的{position}是谁？", response_model=AUTHOR, map_keys=["book",])
input = [
    "《红楼梦》",
    "《西游记》",
    "《三国演义》",
    "《水浒传》",
]
print(llm(book=input, position="作者"))
```

也可以使用 [Tools](../Agent/tools.md) 来批量调用工具（似乎这个需求不太重要，误）。
