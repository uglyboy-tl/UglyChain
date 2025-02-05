from __future__ import annotations

# ReAct 的系统提示模板
REACT_SYSTEM_PROMPT = """You are an expert assistant who can solve any task using tools. You will be given a task to solve as best you can.
To do so, you have been given access to the following tools: [{tool_names}].

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

Thought: Always consider the appropriate course of action.
Action: Choose one action from [{tool_names}]
Action Input: Format the input using XML-style tags, with each parameter enclosed in its own set of tags (e.g. <text>hello world</text>\n<num_beams>5</num_beams>)
Observation: The result of the action.

... (this Thought/Action/Action Input/Observation can be repeated zero or more times)

Thought: I now know the final answer
Action: final_answer
Action Input: <answer>final answer</answer>
```

## Tools
{tool_descriptions}

## Instructions
1. ALWAYS provide a tool call, else you will fail.
2. Always use the right arguments for the tools. Never use variable names as the action arguments, use the value instead.
3. Call a tool only when needed: do not call the search agent if you do not need information, try to solve the task yourself. If no tool call is needed, use final_answer tool to return your answer.
4. Never re-do a tool call that you previously did with the exact same parameters.

## Extra instructions
{extra_instructions}
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

RESPONSE_YAML_PROMPT = """## Output Format
**The output must be a YAML object**.

For example, for the schema ```yaml\n$defs:\n  Gender:\n    enum:\n    - FEMALE\n    - MALE\n    title: Gender\n    type: string\nproperties:\n  gender:\n    $ref: '#/$defs/Gender'\n  name:\n    title: Name\n    type: string\nrequired:\n- name\n- gender\n\n```, the object ```yaml\nname: Jason\ngender: MALE\n``` is a well-formatted instance of the schema.

Only Response Your Final YAML, according to the following schema:
```yaml
{schema}
```

Answer:
```yaml\
"""
