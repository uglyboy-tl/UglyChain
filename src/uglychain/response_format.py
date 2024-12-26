from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

# 创建一个泛型变量，用于约束BaseModel的子类
T = TypeVar("T", bound=BaseModel)

PROMPT_TEMPLATE = """The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{model_json_output_prompt}
```

Ensure the response can be parsed by Python json.loads"""


def get_response_format_prompt(model: type[BaseModel]) -> str:
    """
    生成模型的响应格式提示。

    # Args:
        model (BaseModel): 需要生成提示的模型实例。

    # Returns:
        str: 返回响应格式提示字符串。
    """
    global PROMPT_TEMPLATE
    schema = model.model_json_schema()
    # Remove extraneous fields.
    reduced_schema = schema
    if "title" in reduced_schema:
        del reduced_schema["title"]
    if "type" in reduced_schema:
        del reduced_schema["type"]
    prompt = json.dumps(reduced_schema, ensure_ascii=False)
    return PROMPT_TEMPLATE.format(model_json_output_prompt=prompt)


def from_response(model: type[T], response: str) -> T:
    try:
        match = re.search(r"(\{.*\})", response.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
        json_str = ""
        if match:
            json_str = match.group()
        return model.model_validate_json(json_str)

    except (json.JSONDecodeError, ValidationError) as e:
        name = model.__name__
        msg = f"Failed to parse {name} from completion {response}. Got: {e}"
        raise ValueError(msg) from e
