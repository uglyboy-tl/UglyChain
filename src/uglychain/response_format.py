from __future__ import annotations

import inspect
import json
import re
from collections.abc import Callable
from enum import Enum, unique
from typing import Any, Generic, TypeVar, get_type_hints

from openai.lib import _pydantic
from pydantic import BaseModel, Field, ValidationError


class ToolResopnse(BaseModel):
    name: str
    args: dict


# 创建一个泛型变量，用于约束BaseModel的子类
T = TypeVar("T", bound=BaseModel)


@unique
class Mode(Enum):
    TOOLS = "tool_call"
    MD_JSON = "markdown_json_mode"
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

Make sure to return an instance of the JSON which can be parsed by Python json.loads, not the schema itself."""

    def __init__(self, func: Callable, response_model: type[T] | None = None) -> None:
        # 获取被修饰函数的返回类型
        response_type = get_type_hints(func).get("return", str if response_model is None else response_model)
        self.response_type: type[str] | type[T] = str if response_type is list[dict[str, str]] else response_type
        self.mode: Mode = Mode.MD_JSON
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
        provider, model_name = model.split(":", 1)
        match (provider, model_name):
            case ("openai", ""):
                self.mode = Mode.JSON_SCHEMA
            case ("openai", "yi-large"):
                merged_api_params["response_format"] = {"type": "json_object"}
                self.mode = Mode.MD_JSON
            case ("openai", _):
                self.mode = Mode.TOOLS
            case ("openrouter", "openai/gpt-4o" | "openai/gpt-4o-mini"):
                self.mode = Mode.JSON_SCHEMA
            case ("openrouter", _):
                self.mode = Mode.TOOLS
            case ("ollama" | "gemini", _):
                self.mode = Mode.JSON_SCHEMA
            case _:
                self.mode = Mode.MD_JSON

        match self.mode:
            case Mode.JSON_SCHEMA:
                self._set_response_format_from_params(merged_api_params)
            case Mode.TOOLS:
                self._set_tools_from_params(merged_api_params)
            case Mode.MD_JSON:
                self._update_markdown_json_schema_from_system_prompt(messages)

    def parse_from_response(self, choice: Any, use_tools: bool = False) -> str | T | ToolResopnse:
        # USE TOOLS
        if use_tools and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            tool_calls_response = choice.message.tool_calls[0].function
            tool_response = ToolResopnse(name=tool_calls_response.name, args=json.loads(tool_calls_response.arguments))
            return tool_response
        # Other modes
        if self.response_type is str:
            return choice.message.content.strip()
        assert issubclass(self.response_type, BaseModel) and not inspect.isabstract(self.response_type)
        if self.mode == Mode.MD_JSON or self.mode == Mode.JSON_SCHEMA:
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

    def _update_markdown_json_schema_from_system_prompt(self, messages: list[dict[str, str]]) -> None:
        if not messages:
            raise ValueError("Messages is empty")

        system_prompt = self.PROMPT_TEMPLATE.format(output_schema=json.dumps(self.parameters, ensure_ascii=False))
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

    def _set_response_format_from_params(self, api_params: dict[str, Any]) -> None:
        api_params["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": self.response_type.__name__,
                "schema": self.parameters,
                "strict": True,
            },
        }

    def _set_tools_from_params(self, api_params: dict[str, Any]) -> None:
        api_params["tools"] = [
            {
                "type": "function",
                "function": self.openai_schema,
            }
        ]
        api_params["tool_choice"] = {
            "type": "function",
            "function": {"name": self.openai_schema["name"]},
        }

    @property
    def schema(self) -> dict[str, Any]:
        if hasattr(self, "_schema"):
            return self._schema
        assert inspect.isclass(self.response_type) and issubclass(self.response_type, BaseModel)
        self._schema: dict[str, Any] = self.response_type.model_json_schema()
        return self._schema

    @property
    def parameters(self) -> dict[str, Any]:
        if hasattr(self, "_parameters"):
            return self._parameters
        assert inspect.isclass(self.response_type) and issubclass(self.response_type, BaseModel)
        self._parameters: dict[str, Any] = _pydantic.to_strict_json_schema(self.response_type)
        return self._parameters

    @property
    def openai_schema(self) -> dict[str, Any]:
        if hasattr(self, "_openai_schema"):
            return self._openai_schema
        self._openai_schema: dict[str, Any] = {
            "name": self.schema["title"],
            "parameters": self.parameters,
            "strict": True,
        }
        if self.response_type.__doc__ is not None and self.response_type.__doc__.strip():
            self._openai_schema["description"] = self.response_type.__doc__
        else:
            self._openai_schema["description"] = (
                f"Correctly extracted `{self.schema['title']}` with all the required parameters with correct types"
            )

        return self._openai_schema
