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
    ⚡ UglyChain: A Better LLM Application Development Framework ⚡
    <br />
    <a href="README_zh.md"><strong>中文版本说明 »</strong></a>
    <br />
    <br />
    <a href="https://github.com/uglyboy-tl/UglyChain/issues">Report Bug</a>
    ·
    <a href="https://github.com/uglyboy-tl/UglyChain/issues">Request Feature</a>
  </p>
</div>

## 🤔 What is UglyChain?

UglyChain is a Python framework designed to simplify LLM application development. It provides a more intuitive and developer-friendly interface compared to traditional LLM frameworks.

### Key Problems Addressed:
1. **Non-intuitive API Design**: Many existing frameworks have complex and non-intuitive interfaces
2. **Over-encapsulation**: Excessive abstraction makes customization difficult
3. **Chat-centric Design**: Most frameworks are designed around chat interfaces, which are not ideal for structured application development

### Why Choose UglyChain?
- 🚀 **Developer-friendly API**: Intuitive decorator-based interface
- 🧩 **Modular Design**: Easy to extend and customize
- ⚡ **High Performance**: Built-in support for parallel processing
- 📦 **Production-ready**: Well-documented and thoroughly tested

## ✨ Features

- **Decorator-based API**: Simplify LLM interactions with intuitive decorators
  ```python
  @llm(model="openai:gpt-4o")
  def generate_text(prompt: str) -> str:
      return prompt
  ```

- **Structured Output**: Easily parse LLM responses into structured data
  ```python
  class User(BaseModel):
      name: str
      age: int

  @llm(model="openai:gpt-4o", response_format=User)
  def parse_user(text: str) -> User:
      return text
  ```

- **Parallel Processing**: Process multiple inputs concurrently
  ```python
  @llm(model="openai:gpt-4", map_keys=["input"])
  def batch_process(inputs: list[str]) -> list[str]:
      return inputs
  ```

- **ReAct Support**: Built-in support for reasoning and acting
  ```python
  @react(model="openai:gpt-4", tools=[web_search])
  def research(topic: str) -> str:
      return f"Research about {topic}"
  ```

- **Extensible Architecture**: Easily add custom models and tools

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip 20.0+

### Installation

```bash
# Install from PyPI
pip install uglychain

# Install from source
git clone https://github.com/uglyboy-tl/UglyChain.git
cd UglyChain
pip install -e .
```

### Project Structure

```
uglychain/
├── src/uglychain         # Source code
│   ├── client.py         # Client supported by aisuite
│   ├── config.py         # Configuration management
│   ├── console.py        # Console interface
│   ├── llm.py            # Core LLM functionality
│   ├── react.py          # ReAct implementation
│   ├── structured.py     # Structured output
│   └── tools.py          # Built-in tools
├── tests/                # Unit tests
├── examples/             # Usage examples
├── pyproject.toml        # Build configuration
└── README.md             # Project documentation
```

## Usage

### llm

> A basic decorator that makes it easy to decorate LLM calls for more convenient invocation.

Quick start:

```python
from uglychain import llm

@llm(model="openai:gpt-4o-mini", temperature=0.1)
def hello(world : str):
    """You are a helpful assistant that writes in lower case.""" # System Message
    return f"Say hello to {world[::-1]} with a poem."    # User Message

hello("sama")
```

Structured output example:

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

> Allows batch processing of models through map_keys, returning multiple results. If config.use_parallel_processing is set to True, it will use multiprocessing for parallel execution.

Quick start:

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

Similar to LLM, MapChain can also be used for more advanced scenarios:

```python
class AUTHOR(BaseModel):
    name: str = Field(..., description="Name")
    introduction: str = Field(..., description="Introduction")

@llm("openai:gpt-4o-mini", map_keys=["book"], response_format=AUTHOR)
def map(book: list[str], position: str):
    return f"Who is the {position} of {book}?"

input = [
    "Dream of the Red Chamber",
    "Journey to the West",
    "Romance of the Three Kingdoms",
    "Water Margin",
]
map(book=input, position="author") # Returns a list of AUTHOR objects
```

### ReActChain
> ReActChain is a method for tool invocation using ReAct capability, which performs better than traditional Function Call approaches.

```python
from uglychain import react
from examples.utils import execute_command

@react("openai:gpt-4o-mini", tools = [execute_command])
def update():
    return "Update my computer system"

update() # Automatically runs shell commands to update the system
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

We maintain 100% test coverage for all core functionality.

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Read our [Contribution Guidelines](CONTRIBUTING.md)
2. Fork the repository
3. Create a feature branch (`git checkout -b feature/YourFeature`)
4. Commit your changes (`git commit -m 'Add some feature'`)
5. Push to the branch (`git push origin feature/YourFeature`)
6. Open a Pull Request

### Development Setup

1. Install development dependencies:
   ```bash
   pdm install -G dev
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Run tests before committing:
   ```bash
   pytest
   ```

Please ensure your code:
- Follows PEP 8 style guidelines
- Includes type hints
- Has corresponding unit tests
- Includes documentation

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

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
