"""
prompt模块提供了用于构建提示模板的工具，包括JSON和YAML格式的输出模板，
以及用于构建系统提示的SystemPrompt类。
"""

from __future__ import annotations

from dataclasses import dataclass, field  # 导入dataclass和field，用于数据类定义
from functools import cached_property  # 导入cached_property，用于缓存属性计算结果

from .config import config  # 从当前包导入配置

# 定义输出格式的提示模板，包含对JSON schema的描述和示例
RESPONSE_JSON_PROMPT = """## Output Format
The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{output_schema}
```

Make sure to return an instance of the JSON which can be parsed by Python json.loads, not the schema itself."""

# YAML格式的输出格式提示模板
RESPONSE_YAML_PROMPT = """## Output Format
**The output must be a YAML object**.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object\n```yaml\nfoo:\n  - bar\n  - baz\n```\nis a well-formatted instance of the schema. The object\n```yaml\nproperties:\n  foo:\n    - bar\n    - baz\n```\nis not well-formatted.

Only Response Your Final YAML, according to the following schema:
```
{output_schema}
```

Answer:
```yaml\
"""


@dataclass
class SystemPrompt:
    """
    SystemPrompt类用于构建结构化的系统提示。

    该类提供了一种标准化的方式来创建系统提示，包括角色、目标、描述和指令列表。
    它会自动添加语言指令，并生成格式化的提示文本。
    """

    role: str  # 助手的角色
    objective: str  # 任务目标
    description: str = ""  # 任务描述
    instructions: list[str] = field(default_factory=list)  # 指令列表
    language: str = ""  # 响应语言

    def __post_init__(self) -> None:
        """
        初始化后处理，设置语言并添加语言指令。

        如果未指定语言，则使用配置中的默认语言。
        自动将语言指令添加到指令列表中。
        """
        self.language = self.language or config.default_language  # 使用默认语言
        language_instruction = f"The response must be in {self.language}."  # 创建语言指令
        self.instructions.append(language_instruction)  # 添加到指令列表

    @cached_property
    def prompt(self) -> str:
        """
        生成格式化的提示文本。

        将角色、目标、描述和指令组合成一个结构化的提示文本。
        使用缓存属性以避免重复计算。

        Returns:
            str: 格式化的提示文本
        """
        # 基本提示，包含角色和目标
        prompt = f"You are {self.role} to solve the task: {self.objective}"

        # 添加描述（如果有）
        if self.description:
            prompt += f"\n\n{self.description}"

        # 添加指令列表（如果有）
        if self.instructions:
            _prompt = """\n## Instructions"""
            for i, instruction in enumerate(self.instructions):
                _prompt += f"\n{i + 1}. {instruction}"
            prompt += _prompt

        return prompt

    def __repr__(self) -> str:
        """
        返回提示文本作为对象的字符串表示。

        Returns:
            str: 提示文本
        """
        return self.prompt
