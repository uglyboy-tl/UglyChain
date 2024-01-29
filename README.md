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

- 📦 对大模型接口进行封装，提供对工程化更加直观易懂的交互方式，而不是传统的对话式交互。
  - 可以参数化 Prompt，更加方便地进行批量调用
  - 可以对 Prompt 进行结构化返回，方便后续处理
  - 可以对 Prompt 进行角色设置，方便模型进行角色扮演（这个过程无需操控 Message）
- 🔗 对大模型的高级调用进行封装，提供更加方便的交互方式
  - 提供了类似于 MapReduce 的功能，可以通过 MapChain 对多个 Prompt 进行并行调用，也可以用 ReduceChain 对多个 Prompt 进行串行调用
  - 大模型最优质的能力之一就是拥有 ReAct 能力。我们提供了 ReActChain 便捷的实现这种能力。
- 💾 提供了搜索引擎的封装，可以方便地进行搜索引擎的调用。
  - 注意我们只封装了搜索过程的调用，而没有提供搜索引擎的搭建。如果要构建基于 RAG 的应用，需要利用其他的工具完成资料库的建立，而我们只提供对资料库搜索功能的封装。

## Getting Started

With pip:

```bash
pip install uglychain
```

## Usage

### LLM

> 这是最基础的模型调用类，其他的高级类也都继承和使用了这个类的基本功能。

快速使用：

```python
from uglychain import LLM, Model

llm = LLM()
print(llm("你是谁？")) # 与模型对话，返回字符串的回答
```

调整基础配置选项：

```python
llm = LLM(model = Model.YI) # 可以选择更多的模型，如 Model.GPT3_TURBO、Model.GPT4 等等
llm = LLM(system_prompt = "我想让你担任职业顾问。我将为您提供一个在职业生涯中寻求指导的人，您的任务是帮助他们根据自己的技能、兴趣和经验确定最适合的职业。您还应该对可用的各种选项进行研究，解释不同行业的就业市场趋势，并就哪些资格对追求特定领域有益提出建议。") # 可以对模型设置角色，这样模型就会以这个角色的视角来回答问题。设置的内容保存在 System Message 中。
```

参数化 prompt：

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

结构化返回结果：

```python
class UserDetail(BaseModel):
    name: str
    age: int

llm = LLM(response_model=UserDetail)
print(llm("Extract Jason is 25 years old")) # UserDetail(name='Jason', age=25)
```

### MapChain

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

## Roadmap

- [x] 增加 FunctionCall 的能力
- [ ] 增加 Memory 的能力

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