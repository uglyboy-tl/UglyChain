# 基础 LLM 模块

```python
from uglychain import LLM, Model

llm = LLM()
print(llm("你是谁？")) # 与模型对话，返回字符串的回答
```

## 基础配置

```python
llm = LLM(model = Model.YI) # 可以选择更多的模型，如 Model.GPT3_TURBO、Model.GPT4 等等
llm = LLM(system_prompt = "我想让你担任职业顾问。我将为您提供一个在职业生涯中寻求指导的人，您的任务是帮助他们根据自己的技能、兴趣和经验确定最适合的职业。您还应该对可用的各种选项进行研究，解释不同行业的就业市场趋势，并就哪些资格对追求特定领域有益提出建议。") # 可以对模型设置角色，这样模型就会以这个角色的视角来回答问题。设置的内容保存在 System Message 中。
```

## 参数化 Prompt

```python
llm = LLM(prompt_template = "{object}的{position}是谁？")
print(llm(object = "《红楼梦》", position = "作者"))
print(llm(object = "上海市", position = "市长"))
```

对于 prompt 中只有一个参数的情况，可以直接传入参数：

```python
llm = LLM("介绍一下{object}")
print(llm("Transformer"))
```

## 结构化返回结果

```python
class UserDetail(BaseModel):
    name: str
    age: int

llm = LLM(response_model=UserDetail)
print(llm("Extract Jason is 25 years old")) # UserDetail(name='Jason', age=25)
```

参见 [结构化输出](../Agent/structured.md)

## 使用工具

参见 [工具](../Agent/tools.md)。

## 设置模型细节参数

我们可以通过直接修改 `llm` 的参数来设置模型的细节参数，支持的参数如下：

- `custom_model_name`：自定义模型名称。
- `temperature`：温度参数。
- `top_p`：top-p 参数。
- `frequency_penalty`：频率惩罚参数。
- `presence_penalty`：存在惩罚参数。
- `seed`：随机种子。

需要注意不同的模型对参数的支持情况可能不同，包括参数的名称和取值范围。

```python
llm = LLM()
llm.temperature = 0.5
llm.top_p = 0.9
llm.frequency_penalty = 0.5
llm.presence_penalty = 0.5
llm.seed = 42
```
