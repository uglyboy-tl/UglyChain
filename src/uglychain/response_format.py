from __future__ import annotations

import inspect
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


class ResponseModel(Generic[T]):
    # 定义输出格式的提示模板，包含对JSON schema的描述和示例
    PROMPT_TEMPLATE = """The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{output_schema}
```

Ensure the response can be parsed by Python json.loads"""

    def __init__(self, func: Callable, response_model: type[T] | None = None) -> None:
        # 获取被修饰函数的返回类型
        self.response_type: type[str] | type[list[dict[str, str]]] | type[T] = get_type_hints(func).get(
            "return", str if response_model is None else response_model
        )
        if self.response_type is list[dict[str, str]]:
            self.response_type = str
        assert self.response_type is response_model or self.response_type is str
        self.mode: Mode = Mode.JSON
        self.validate_response_type()

    def validate_response_type(self) -> None:
        if self.response_type is not str and not issubclass(self.response_type, BaseModel):
            raise TypeError(f"Unsupported return type: {self.response_type}")

    def process_parameters(
        self,
        model: str,
        messages: list[dict[str, str]],
        merged_api_params: dict[str, Any],
    ) -> None:
        if self.response_type is str:
            return
        provider, model_name = model.split(":")
        if provider in ["openai"]:
            if model_name in []:  # "gpt-4o", "gpt-4o-mini"支持这个能力, 但解析函数需要更换，现在 AiSuite 不支持
                self.mode = Mode.JSON_SCHEMA
                merged_api_params["response_format"] = self.get_response_schema()
            elif model_name in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]:
                self.mode = Mode.TOOLS
            else:
                merged_api_params["response_format"] = {"type": "json_object"}
        elif provider in ["ollama"]:
            self.mode = Mode.JSON_SCHEMA
            merged_api_params["format"] = self.get_response_schema()
        if self.mode == Mode.JSON:
            self.update_system_prompt_to_json(messages)
        elif self.mode == Mode.TOOLS:
            self.update_params_to_tools(merged_api_params)

    def parse_from_response(self, choice: Any, use_tools: bool = False) -> str | T:
        # USE TOOLS
        if use_tools and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            tool_calls_response = choice.message.tool_calls[0].function
            return json.dumps({"name": tool_calls_response.name, "args": json.loads(tool_calls_response.arguments)})
        # Other modes
        if self.response_type is str:
            return choice.message.content.strip()
        assert issubclass(self.response_type, BaseModel) and not inspect.isabstract(self.response_type)
        if self.mode == Mode.JSON or self.mode == Mode.JSON_SCHEMA:
            response = choice.message.content.strip()
        elif self.mode == Mode.TOOLS:
            response = choice.message.tool_calls[0].function.arguments
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

        try:
            # 尝试直接解析整个响应字符串
            json_obj = json.loads(response.strip())
            return self.response_type.model_validate_json(json.dumps(json_obj))  # type: ignore[union-attr]

        except json.JSONDecodeError:
            # 如果直接解析失败，尝试使用正则表达式提取 JSON 字符串
            match = re.search(r"(\{.*\})", response.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if match:
                json_str = match.group()
                try:
                    return self.response_type.model_validate_json(json_str)  # type: ignore[union-attr]
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

    def get_response_schema(self) -> str:
        # 获取模型的JSON schema
        assert issubclass(self.response_type, BaseModel)
        schema = self.response_type.model_json_schema()  # type: ignore[union-attr]
        # 移除不必要的字段，减少提示的冗余信息
        reduced_schema = schema.copy()
        if "title" in reduced_schema:
            del reduced_schema["title"]
        if "type" in reduced_schema:
            del reduced_schema["type"]
        reduced_schema["required"] = sorted(k for k, v in reduced_schema["properties"].items() if "default" not in v)
        # 将简化后的schema转换为JSON字符串
        prompt = json.dumps(reduced_schema, ensure_ascii=False)
        # 格式化并返回提示字符串
        return prompt

    def update_system_prompt_to_json(self, messages: list[dict[str, str]]) -> None:
        if not messages:
            raise ValueError("Messages is empty")

        system_prompt = self.PROMPT_TEMPLATE.format(output_schema=self.get_response_schema())
        system_message = messages[0]
        if system_message["role"] == "system":
            system_message["content"] += "\n-----\n" + system_prompt
        else:
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": system_prompt,
                },
            )

    def update_params_to_tools(self, api_params: dict[str, Any]) -> None:
        assert issubclass(self.response_type, BaseModel)
        schema = self.response_type.model_json_schema()  # type: ignore[union-attr]
        api_params["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": schema["title"],
                    "description": f"Correctly extracted `{schema['title']}` with all the required parameters with correct types",
                    "parameters": {k: v for k, v in schema.items() if k not in ("title", "description")},
                    "strict": True,
                },
            }
        ]
        api_params["tool_choice"] = {
            "type": "function",
            "function": {"name": schema["title"]},
        }
