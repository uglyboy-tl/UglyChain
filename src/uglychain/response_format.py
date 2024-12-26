from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

# 创建一个泛型变量，用于约束BaseModel的子类
T = TypeVar("T", bound=BaseModel)


class ResponseFormatter:
    # 定义输出格式的提示模板，包含对JSON schema的描述和示例
    PROMPT_TEMPLATE = """The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{model_json_output_prompt}
```

Ensure the response can be parsed by Python json.loads"""

    @staticmethod
    def get_response_format_prompt(model: type[T]) -> str:
        """
        生成模型的响应格式提示。

        Args:
            model (type[T]): 需要生成提示的模型类。

        Returns:
            str: 返回响应格式提示字符串。
        """
        # 获取模型的JSON schema
        schema = model.model_json_schema()
        # 移除不必要的字段，减少提示的冗余信息
        reduced_schema = schema.copy()
        if "title" in reduced_schema:
            del reduced_schema["title"]
        if "type" in reduced_schema:
            del reduced_schema["type"]
        # 将简化后的schema转换为JSON字符串
        prompt = json.dumps(reduced_schema, ensure_ascii=False)
        # 格式化并返回提示字符串
        return ResponseFormatter.PROMPT_TEMPLATE.format(model_json_output_prompt=prompt)

    @staticmethod
    def parse_model_from_response(model: type[T], response: str) -> T:
        """
        从响应字符串中解析并验证模型实例。

        Args:
            model (type[T]): 模型类，用于解析和验证响应。
            response (str): 响应字符串，可能包含JSON格式的数据。

        Returns:
            T: 解析并验证后的模型实例。

        Raises:
            ValueError: 如果解析或验证失败，抛出此异常。
        """
        try:
            # 尝试直接解析整个响应字符串
            json_obj = json.loads(response.strip())
            return model.model_validate_json(json.dumps(json_obj))

        except json.JSONDecodeError:
            # 如果直接解析失败，尝试使用正则表达式提取 JSON 字符串
            match = re.search(r"(\{.*\})", response.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if match:
                json_str = match.group()
                try:
                    return model.model_validate_json(json_str)
                except (json.JSONDecodeError, ValidationError) as e:
                    # 如果解析或验证失败，记录错误信息并抛出异常
                    name = model.__name__
                    msg = f"Failed to parse {name} from completion {response}. Got: {e}"
                    raise ValueError(msg) from e
            else:
                # 如果正则表达式匹配失败，抛出异常
                name = model.__name__
                raise ValueError(f"Failed to find JSON object in response for {name}: {response}") from None

        except ValidationError as e:
            # 如果验证失败，记录错误信息并抛出异常
            name = model.__name__
            msg = f"Failed to validate {name} from completion {response}. Got: {e}"
            raise ValueError(msg) from e
