# 高级 Chain 模块

## MapChain

> 这是一个可以并行对同类型 Prompt 进行调用的类，可以大大提高调用效率。

快速使用：

```python
from uglychain import MapChain

llm = MapChain()
print(llm([
        {"input": "How old are you?"},
        {"input": "What is the meaning of life?"},
        {"input": "What is the hottest day of the year?"},
    ]))
```

类似于 LLM，也可以对 MapChain 进行更高阶的使用：

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