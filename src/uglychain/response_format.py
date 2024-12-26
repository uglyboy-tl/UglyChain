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

    models_mode: dict[str, Mode] = {}

    @staticmethod
    def validate_response(func: Callable) -> type[str] | type[T]:
        """
        验证响应字符串是否为有效的模型实例。
        """
        # 获取被修饰函数的返回类型
        return_type = get_type_hints(func).get("return", str)
        if return_type is not str and not issubclass(return_type, BaseModel):
            raise TypeError(f"Unsupported return type: {return_type}")
        if return_type is str:
            return str
        return cast(type[T], return_type)

    @staticmethod
    def _get_response_format_prompt(response_type: type[T]) -> str:
        """
        生成模型的响应格式提示。

        Args:
            model (type[T]): 需要生成提示的模型类。

        Returns:
            str: 返回响应格式提示字符串。
        """
        # 获取模型的JSON schema
        schema = response_type.model_json_schema()
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
    def parse_model_from_response(response_type: type[T], choice: Any, model: str) -> T:
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
        mode = ResponseFormatter.models_mode.get(model, Mode.JSON)
        if mode == Mode.JSON or mode == Mode.JSON_SCHEMA:
            response = choice.message.content.strip()
        elif mode == Mode.TOOLS:
            response = choice.message.tool_calls[0].function.arguments
        else:
            raise ValueError(f"Unsupported mode: {mode}")
        try:
            # 尝试直接解析整个响应字符串
            json_obj = json.loads(response.strip())
            return response_type.model_validate_json(json.dumps(json_obj))

        except json.JSONDecodeError:
            # 如果直接解析失败，尝试使用正则表达式提取 JSON 字符串
            match = re.search(r"(\{.*\})", response.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if match:
                json_str = match.group()
                try:
                    return response_type.model_validate_json(json_str)
                except (json.JSONDecodeError, ValidationError) as e:
                    # 如果解析或验证失败，记录错误信息并抛出异常
                    name = response_type.__name__
                    msg = f"Failed to parse {name} from completion {response}. Got: {e}"
                    raise ValueError(msg) from e
            else:
                # 如果正则表达式匹配失败，抛出异常
                name = response_type.__name__
                raise ValueError(f"Failed to find JSON object in response for {name}: {response}") from None

        except ValidationError as e:
            # 如果验证失败，记录错误信息并抛出异常
            name = response_type.__name__
            msg = f"Failed to validate {name} from completion {response}. Got: {e}"
            raise ValueError(msg) from e

    @staticmethod
    def _update_system_prompt_to_json(messages: list[dict[str, str]], response_type: type[T]) -> None:
        """
        更新系统提示，添加响应格式提示。
        """
        system_message = messages[0]
        if system_message["role"] == "system":
            system_message["content"] += "\n-----\n" + ResponseFormatter._get_response_format_prompt(response_type)
        else:
            system_message = {
                "role": "system",
                "content": ResponseFormatter._get_response_format_prompt(response_type),
            }
            messages.insert(0, system_message)

    @staticmethod
    def _update_params_to_tools(api_params: dict[str, Any], response_type: type[T]) -> None:
        schema = response_type.model_json_schema()
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

    @staticmethod
    def process_parameters(
        messages: list[dict[str, str]], merged_api_params: dict[str, Any], return_type: type[T], model: str
    ):
        # TODO: 可以选择用怎样的方式实现结构化输出，当前只实现了基于 Prompt 的方式
        provider, model_name = model.split(":")
        mode: Mode = Mode.JSON
        if provider in ["openai"]:
            if model_name in []:  # "gpt-4o", "gpt-4o-mini"支持, 但解析函数需要更换
                mode = Mode.JSON_SCHEMA
                merged_api_params["response_format"] = ResponseFormatter._get_response_format_prompt(return_type)
            elif model_name in ["gpt-4o", "gpt-4o-mini"]:
                mode = Mode.TOOLS
            else:
                merged_api_params["response_format"] = {"type": "json_object"}
        elif provider in ["ollama"]:
            mode = Mode.JSON_SCHEMA
            merged_api_params["format"] = ResponseFormatter._get_response_format_prompt(return_type)
        if mode == Mode.JSON:
            ResponseFormatter._update_system_prompt_to_json(messages, return_type)
        elif mode == Mode.TOOLS:
            ResponseFormatter._update_params_to_tools(merged_api_params, return_type)
        ResponseFormatter.models_mode[model] = mode
