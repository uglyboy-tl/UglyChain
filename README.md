[![Release Notes][release-shield]][release-url]
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/uglyboy-tl/UglyChain">
    <!-- <img src="images/logo.png" alt="Logo" width="80" height="80"> -->
  </a>

  <h3 align="center">UglyChain</h3>

  <p align="center">
    ⚡ UglyChain：更好用的 LLM 应用构建工具 ⚡
    <br />
    <a href="https://uglychain.uglyboy.cn"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/uglyboy-tl/UglyChain/issues">Report Bug</a>
    ·
    <a href="https://github.com/uglyboy-tl/UglyChain/issues">Request Feature</a>
  </p>
</div>

## 🤔 What is UglyChain?
现在有很多利用大模型 LLM 进行应用构建的工具，最有名的就是 LangChain。早期的 LangChain 整个框架并不完善，很多并不直观的定义和调用方式，以及将内部功能封装得太彻底，使的难以定制化的更充分的利用大模型的能力来解决问题。所以我就开发的最初的 UglyGPT（UglyChain的原型），试图解决这个问题。

到了今天，GPTs 也已经面世很长时间了，也有了越来越多的 LLM 应用构建工具。但是这些工具都有一个共同的问题：**不够直观**。
从底层来说，现在的大模型是基于 Chat 进行接口交互的，这对于应用开发而言并不友好，因为应用开发更多的是模板化的结构化内容生成，而不是对话式的交互。所以我们需要一个对应用开发更加友好的接口，这就是 UglyChain 的初衷。

## Features
感谢 [aisuite](https://github.com/andrewyng/aisuite) 项目，为 UglyChain 的开发提供了对原始 LLM 接口的初步封装。感谢 [ell](https://docs.ell.so/) 项目，UglyChain 的设计主要借鉴了 ell 的 “Prompts are programs, not strings” 思想，参考其修饰器的实现思路，进一步实现了 mapchain、结构化输出 和 ReActChain 等功能。

- 📦 对大模型接口进行封装，提供对工程化更加直观易懂的交互方式，而不是传统的对话式交互。
  - 可以参数化 Prompt，更加方便地进行批量调用
  - 可以对 Prompt 进行结构化返回，方便后续处理
- 🔗 对大模型的高级调用进行封装，提供更加方便的交互方式
  - 可以通过 @llm 的 map_key 对多个 Prompt 进行并行调用;
  - 大模型最优质的能力之一就是拥有 ReAct 能力。我们提供了 @react 便捷的实现这种能力。

## Getting Started

With pip:

```bash
pip install uglychain
```

## Usage

### llm

> 这是一个基础的修饰器，可以方便的对 LLM 进行修饰，使得调用更加方便。

快速使用：

```python
from uglychain import llm

@llm(model="openai:gpt-4o-mini", temperature=0.1)
def hello(world : str):
    """You are a helpful assistant that writes in lower case.""" # System Message
    return f"Say hello to {world[::-1]} with a poem."    # User Message

hello("sama")
```

结构化返回结果：

```python
class UserDetail(BaseModel):
    name: str
    age: int

@llm("openai:gpt-4o-mini", response_format=UserDetail)
def test(name: str):
    return f"{name} is a boy"

test("Bob")
```

### MapChain

> 通过 map_keys 可以对模型进行批量调用，并返回多个结果。如果在 config.use_parallel_processing 中设置为 True，则会使用多进程进行并行调用。

快速使用：

```python
@llm("openai:gpt-4o-mini", map_keys=["input"])
def map(input: list[str]):
    return input

input = [
    "How old are you?",
    "What is the meaning of life?",
    "What is the hottest day of the year?",
]
for item in map(input):
    print(item)
```

类似于 LLM，也可以对 MapChain 进行更高阶的使用：

```python
class AUTHOR(BaseModel):
    name: str = Field(..., description="姓名")
    introduction: str = Field(..., description="简介")

@llm("openai:gpt-4o-mini", map_keys=["book"], response_format=AUTHOR)
def map(book: list[str], position: str):
    return f"{book}的{position}是谁？"

input = [
    "《红楼梦》",
    "《西游记》",
    "《三国演义》",
    "《水浒传》",
]
map(book=input, position="作者") # 返回的是AUTHOR对象的列表
```

### ReActChain
> ReActChain 是使用 ReAct 能力进行工具调用的一种方法，其效果原好于传统的 Function Call 的方式。

```python
from uglychain import react
from examples.utils import execute_command

@react("openai:gpt-4o-mini", tools = [execute_command])
def update():
    return "更新我的电脑系统"

update() # 自动运行 shell 命令，来更新系统
```

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[release-shield]:https://img.shields.io/github/release/uglyboy-tl/UglyChain.svg?style=for-the-badge
[release-url]: https://github.com/uglyboy-tl/UglyChain/releases
[contributors-shield]: https://img.shields.io/github/contributors/uglyboy-tl/UglyChain.svg?style=for-the-badge
[contributors-url]: https://github.com/uglyboy-tl/UglyChain/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/uglyboy-tl/UglyChain.svg?style=for-the-badge
[forks-url]: https://github.com/uglyboy-tl/UglyChain/network/members
[stars-shield]: https://img.shields.io/github/stars/uglyboy-tl/UglyChain.svg?style=for-the-badge
[stars-url]: https://github.com/uglyboy-tl/UglyChain/stargazers
[issues-shield]: https://img.shields.io/github/issues/uglyboy-tl/UglyChain.svg?style=for-the-badge
[issues-url]: https://github.com/uglyboy-tl/UglyChain/issues
[license-shield]: https://img.shields.io/github/license/uglyboy-tl/UglyChain.svg?style=for-the-badge
[license-url]: https://github.com/uglyboy-tl/UglyChain/blob/master/LICENSE.txt
