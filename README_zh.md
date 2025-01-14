[![Docs][docs-shield]][docs-url]
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
    ⚡ UglyChain：更好的 LLM 应用开发框架 ⚡
    <br />
    <a href="README.md"><strong>English version README »</strong></a>
    <br />
    <br />
    <a href="https://github.com/uglyboy-tl/UglyChain/issues">报告问题</a>
    ·
    <a href="https://github.com/uglyboy-tl/UglyChain/issues">请求功能</a>
  </p>
</div>

## 🤔 什么是 UglyChain？

UglyChain 是一个旨在简化 LLM 应用开发的 Python 框架。它提供了比传统 LLM 框架更直观、对开发者更友好的接口。

### 解决的关键问题：
1. **非直观的 API 设计**：许多现有框架具有复杂且不直观的接口
2. **过度封装**：过多的抽象使得定制变得困难
3. **以聊天为中心的设计**：大多数框架围绕聊天接口设计，这不适合结构化应用开发

### 为什么选择 UglyChain？
- 🚀 **开发者友好的 API**：直观的基于装饰器的接口
- 🧩 **模块化设计**：易于扩展和定制
- ⚡ **高性能**：内置并行处理支持
- 📦 **生产就绪**：文档完善且经过全面测试

## ✨ 功能特性

- **基于装饰器的 API**：使用直观的装饰器简化 LLM 交互
  ```python
  @llm(model="openai:gpt-4o")
  def generate_text(prompt: str) -> str:
      return prompt
  ```

- **结构化输出**：轻松将 LLM 响应解析为结构化数据
  ```python
  class User(BaseModel):
      name: str
      age: int

  @llm(model="openai:gpt-4o", response_format=User)
  def parse_user(text: str) -> User:
      return text
  ```

- **并行处理**：并发处理多个输入
  ```python
  @llm(model="openai:gpt-4", map_keys=["input"])
  def batch_process(inputs: list[str]) -> list[str]:
      return inputs
  ```

- **ReAct 支持**：内置推理和行动支持
  ```python
  @react(model="openai:gpt-4", tools=[web_search])
  def research(topic: str) -> str:
      return f"Research about {topic}"
  ```

- **可扩展架构**：轻松添加自定义模型和工具

## 🚀 快速开始

### 环境要求
- Python 3.10+
- pip 20.0+

### 安装

```bash
# 从 PyPI 安装
pip install uglychain

# 从源码安装
git clone https://github.com/uglyboy-tl/UglyChain.git
cd UglyChain
pip install -e .
```

### 项目结构

```
uglychain/
├── src/                  # 源代码
│   ├── client.py         # 由 aisuite 支持的客户端
│   ├── config.py         # 配置管理
│   ├── console.py        # 控制台接口
│   ├── llm.py            # 核心 LLM 功能
│   ├── react.py          # ReAct 实现
│   ├── structured.py     # 结构化输出
│   └── tools.py          # 内置工具
├── tests/                # 单元测试
├── examples/             # 使用示例
├── pyproject.toml        # 构建配置
└── README.md             # 项目文档
```

## 使用指南

### llm

> 一个基础装饰器，可以方便地装饰 LLM 调用，使调用更加便捷。

快速开始：

```python
from uglychain import llm

@llm(model="openai:gpt-4o-mini", temperature=0.1)
def hello(world : str):
    """You are a helpful assistant that writes in lower case.""" # 系统消息
    return f"Say hello to {world[::-1]} with a poem."    # 用户消息

hello("sama")
```

结构化输出示例：

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

> 通过 map_keys 实现模型的批量处理，返回多个结果。如果 config.use_parallel_processing 设置为 True，则会使用多进程进行并行执行。

快速开始：

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

与 LLM 类似，MapChain 也可用于更高级的场景：

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
map(book=input, position="作者") # 返回 AUTHOR 对象列表
```

### ReActChain
> ReActChain 是一种使用 ReAct 能力进行工具调用的方法，其性能优于传统的 Function Call 方法。

```python
from uglychain import react
from examples.utils import execute_command

@react("openai:gpt-4o-mini", tools = [execute_command])
def update():
    return "Update my computer system"

update() # 自动运行 shell 命令来更新系统
```

## 🧪 测试

运行测试套件：

```bash
pytest tests/
```

我们为核心功能维护 100% 的测试覆盖率。

## 🤝 贡献指南

我们欢迎贡献！请按照以下步骤操作：

1. 阅读我们的[贡献指南](CONTRIBUTING.md)
2. Fork 仓库
3. 创建功能分支 (`git checkout -b feature/YourFeature`)
4. 提交更改 (`git commit -m '添加新功能'`)
5. 推送分支 (`git push origin feature/YourFeature`)
6. 打开 Pull Request

### 开发环境设置

1. 安装开发依赖：
   ```bash
   pdm install -G dev
   ```

2. 设置 pre-commit 钩子：
   ```bash
   pre-commit install
   ```

3. 提交前运行测试：
   ```bash
   pytest
   ```

请确保您的代码：
- 遵循 PEP 8 风格指南
- 包含类型提示
- 有相应的单元测试
- 包含文档

## 许可证

本项目采用 MIT 许可证。详情请参阅 `LICENSE.txt`。

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[docs-shield]: https://img.shields.io/badge/Docs-mkdocs-blue?style=for-the-badge
[docs-url]: https://uglychain.uglyboy.cn/
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
