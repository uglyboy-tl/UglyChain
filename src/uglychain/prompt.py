from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

from .config import config

# ReAct 的系统提示模板
REACT_SYSTEM_PROMPT = """You are an expert assistant who can solve any task using tools. You will be given a task to solve as best you can.
To do so, you have been given access to the following tools: [{tools_names}].

To solve the task, you must plan forward to proceed in a series of steps, in a cycle of 'Thought:', 'Action:', 'Action Input:', and 'Observation:' sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning towards solving the task and the tools that you want to use.
Then in the 'Action:' and 'Action Input:' sequence, you should tell system what tool to use and what arguments to use.
The action result will then appear in the 'Observation:' field, which will be available as input for the next step. And you do not need to generate this part, it will be automatically filled by the system. The observation will always be a string: it can represent a file, like "image_1.jpg".
In the end you have to return a final answer using the `final_answer` tool.

## Example
An fake example:
```
Task:
the input question you must answer

Thought: Considering the current situation and the overall goal, determine the most effective action to take.
Action: Choose one action from [{tools_names}].  The tool name must be used exactly as provided (do not translate it).
Action Input:  Format the input precisely using XML-style tags.  Each parameter should be enclosed in its own set of tags, and parameter names are case-sensitive.  For example:  `<text>This is the input text.</text>\n<num_beams>5</num_beams>`.  Ensure all required parameters are provided and adhere to any length restrictions.
Observation: Result of the action.

... (this Thought/Action/Action Input/Observation can be repeated zero or more times)

Thought: I now know the final answer
Action: final_answer
Action Input: <answer>final answer</answer>
```

## Tools
{tools_descriptions}

## Instructions
1.  **CRITICAL: You MUST always provide a tool call in each turn, unless you can definitively provide the final answer using the `final_answer` tool. Failure to provide a tool call when needed will result in task failure. If you realize you made a mistake, correct it immediately in the next turn.**
2.  **IMPORTANT: Always use the correct and *actual* values for the tool's arguments. NEVER use variable names, placeholders, or incomplete values. The arguments MUST be formatted as XML-style tags, with each parameter enclosed in its own set of tags (e.g., `<text>hello world</text>\n<num_beams>5</num_beams>`). Ensure all required parameters are present and valid. The values should be derived from the current context, previous observations, or your internal knowledge.**
3.  **Call a tool ONLY when absolutely necessary to gather information or perform a specific action.  Avoid using the `search` tool if you already possess sufficient information to solve the task.  Consider whether you can solve the task using your existing knowledge before resorting to a tool. If no tool call is needed, use the `final_answer` tool to return your answer.**
4.  **AVOID redundant tool calls.  Do NOT re-execute a tool call with the *exact* same parameters as a previous call.  Repeating the same tool call provides no new information and wastes resources. If the previous result was insufficient, consider *different* parameters or a *different* tool.**


## Extra instructions
These instructions SUPPLEMENT or OVERRIDE the previous instructions.  Please pay close attention to them.

{extra_instructions}

You MUST respond STRICTLY in {language}.  Do NOT deviate from the specified language under any circumstances.
"""

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
