from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

from .config import config

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
    role: str
    objective: str
    description: str = ""
    instructions: list[str] = field(default_factory=list)
    language: str = ""

    def __post_init__(self) -> None:
        self.language = self.language or config.default_language
        language_instruction = f"The response must be in {self.language}."
        self.instructions.append(language_instruction)

    @cached_property
    def prompt(self) -> str:
        prompt = f"You are {self.role} to solve the task: {self.objective}"
        if self.description:
            prompt += f"\n\n{self.description}"
        if self.instructions:
            _prompt = """\n## Instructions"""
            for i, instruction in enumerate(self.instructions):
                _prompt += f"\n{i + 1}. {instruction}"
            prompt += _prompt
        return prompt

    def __repr__(self) -> str:
        return self.prompt
