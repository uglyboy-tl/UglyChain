from __future__ import annotations

import json
import re
from collections.abc import Callable
from enum import Enum, unique
from typing import Any, Generic, TypeVar, cast, get_type_hints

from pydantic import BaseModel, ValidationError

# 创建一个泛型变量，用于约束BaseModel的子类
T = TypeVar("T", bound=BaseModel)


@unique
class Mode(Enum):
    TOOLS = "tool_call"
    JSON = "json_mode"
    JSON_SCHEMA = "json_schema_mode"


class ResponseFormatter(Generic[T]):
    # 定义输出格式的提示模板，包含对JSON schema的描述和示例
    PROMPT_TEMPLATE = """The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{model_json_output_prompt}
```

Ensure the response can be parsed by Python json.loads"""

    def __init__(self, func: Callable) -> None:
        """
        验证响应字符串是否为有效的模型实例。
        """
        # 获取被修饰函数的返回类型
        self.response_type: type[str] | type[T] = get_type_hints(func).get("return", str)
        self.mode: Mode = Mode.JSON
        self._validate_response_type()

    def _validate_response_type(self) -> None:
        if self.response_type is not str and not issubclass(self.response_type, BaseModel):
            raise TypeError(f"Unsupported return type: {self.response_type}")

    def _get_response_format_prompt(self) -> str:
        """
        生成模型的响应格式提示。

        Args:
            model (type[T]): 需要生成提示的模型类。

        Returns:
            str: 返回响应格式提示字符串。
        """
        # 获取模型的JSON schema
        assert issubclass(self.response_type, BaseModel)
        schema = self.response_type.model_json_schema()
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

    def parse_from_response(self, choice: Any) -> str | T:
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
        if self.response_type is str:
            return choice.message.content.strip()
        assert issubclass(self.response_type, BaseModel)
        if self.mode == Mode.JSON or self.mode == Mode.JSON_SCHEMA:
            response = choice.message.content.strip()
        elif self.mode == Mode.TOOLS:
            response = choice.message.tool_calls[0].function.arguments
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

        try:
            # 尝试直接解析整个响应字符串
            json_obj = json.loads(response.strip())
            return self.response_type.model_validate_json(json.dumps(json_obj))

        except json.JSONDecodeError:
            # 如果直接解析失败，尝试使用正则表达式提取 JSON 字符串
            match = re.search(r"(\{.*\})", response.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if match:
                json_str = match.group()
                try:
                    return self.response_type.model_validate_json(json_str)
                except (json.JSONDecodeError, ValidationError) as e:
                    # 如果解析或验证失败，记录错误信息并抛出异常
                    name = self.response_type.__name__
                    msg = f"Failed to parse {name} from completion {response}. Got: {e}"
                    raise ValueError(msg) from e
            else:
                # 如果正则表达式匹配失败，抛出异常
                name = self.response_type.__name__
                raise ValueError(f"Failed to find JSON object in response for {name}: {response}") from None

        except ValidationError as e:
            # 如果验证失败，记录错误信息并抛出异常
            name = self.response_type.__name__
            msg = f"Failed to validate {name} from completion {response}. Got: {e}"
            raise ValueError(msg) from e

    def _update_system_prompt_to_json(self, messages: list[dict[str, str]]) -> None:
        """
        更新系统提示，添加响应格式提示。
        """
        if not messages:
            raise ValueError("Messages is empty")

        system_message = messages[0]
        if system_message["role"] == "system":
            system_message["content"] += "\n-----\n" + self._get_response_format_prompt()
        else:
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": self._get_response_format_prompt(),
                },
            )

    def _update_params_to_tools(self, api_params: dict[str, Any]) -> None:
        assert issubclass(self.response_type, BaseModel)
        schema = self.response_type.model_json_schema()
        api_params["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": schema["title"],
                    "description": f"Correctly extracted `{schema['title']}` with all the required parameters with correct types",
                    "parameters": {k: v for k, v in schema.items() if k not in ("title", "description")},
                },
            }
        ]
        api_params["tool_choice"] = {
            "type": "function",
            "function": {"name": schema["title"]},
        }

    def process_parameters(
        self,
        messages: list[dict[str, str]],
        merged_api_params: dict[str, Any],
        model: str,
    ):
        if self.response_type is str:
            return
        provider, model_name = model.split(":")
        if provider in ["openai"]:
            if model_name in []:  # "gpt-4o", "gpt-4o-mini"支持, 但解析函数需要更换
                self.mode = Mode.JSON_SCHEMA
                merged_api_params["response_format"] = self._get_response_format_prompt()
            elif model_name in ["gpt-4o", "gpt-4o-mini"]:
                self.mode = Mode.TOOLS
            else:
                merged_api_params["response_format"] = {"type": "json_object"}
        elif provider in ["ollama"]:
            self.mode = Mode.JSON_SCHEMA
            merged_api_params["format"] = self._get_response_format_prompt()
        if self.mode == Mode.JSON:
            self._update_system_prompt_to_json(messages)
        elif self.mode == Mode.TOOLS:
            self._update_params_to_tools(merged_api_params)
