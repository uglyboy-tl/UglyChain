from dataclasses import dataclass

from uglychain import Model
from uglychain.worker.developer import Developer

ROLE_WRITER = """
假设你是一名高级Python开发者。你的任务是编写一段符合PEP8规范的、优雅的、易于阅读和维护的Python 3.11代码，具体要求如下：
- 根据用户的需求，你需要实现一个完整的代码文件。请注意，你的代码将成为整个项目的一部分，因此需要确保你的代码是完整的、可靠的、并且可以重用。
- 你的代码无需包含注释，但必须符合PEP8规范。
- 文件头需要声明 "#!/usr/bin/env python3"。
- 请尽可能地为变量、函数参数、类的属性、方法等标注数据类型。
- 在编写代码时，优先使用以下Python工具：
    - dataclasses
    - loguru
    - pathlib
"""

ROLE_REVIEWER = """
假设你是一名经验丰富的软件工程师，你的主要任务是审查并优化代码。你需要确保代码符合PEP8标准，设计优雅且模块化，易于阅读和维护，并且是用Python 3.11（或其他编程语言）编写的。具体要求如下：
- 基于`Context`和`Code`，按照下面的检查清单，提供最多5条关键、清晰、简洁和具体的代码修改建议：
    - 检查0：代码是否按照需求实现？
    - 检查1：代码逻辑中是否有任何问题？
    - 检查2：现有代码是否遵循“数据结构和接口定义”？相应的变量是否标注了数据类型？
    - 检查3：代码中是否有遗漏或未完全实现需要实现的函数？
    - 检查4：代码是否有不必要的或缺少的依赖？
- 基于“代码审查”和源代码，你需要尽你最大的努力优化这段代码，使其更加优雅、易于阅读和维护。
- 文件头需要声明 "#!/usr/bin/env python3"。
- 在编写代码时，优先使用以下Python工具：
    - dataclasses
    - loguru
    - pathlib
"""

PROMPT_TEMPLATE = """
## Context
{context}

## Code
```python
{code}
```
"""


@dataclass
class CodeWriter(Developer):
    role: str = ROLE_WRITER
    name: str = "代码开发者"


@dataclass
class CodeReviewer(Developer):
    role: str = ROLE_REVIEWER
    prompt: str = PROMPT_TEMPLATE
    name: str = "代码审查者"


def coder(content: str, model: Model.YI, file_path: str = "data/code/test.py"):
    writer = CodeWriter(model=model, file_path=file_path)
    code = writer.run(context=content)

    reviewer = CodeReviewer(model=model, file_path=file_path)
    reviewer.run(context=content, code=code)


if __name__ == "__main__":
    coder("写一个快速计算圆周率的程序", Model.YI, "data/code/pi.py")
