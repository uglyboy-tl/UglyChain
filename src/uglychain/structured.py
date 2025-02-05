from __future__ import annotations

import inspect
import json
import re
from collections.abc import Callable
from enum import Enum, unique
from typing import Any, Generic, get_origin, get_type_hints

from openai.lib import _pydantic
from pydantic import BaseModel, ValidationError

from .prompt import RESPONSE_JSON_PROMPT
from .schema import Messages, T, ToolResponse


@unique
class Mode(Enum):
    TOOLS = "tool_call"
    MD_JSON = "markdown_json_mode"
    JSON_SCHEMA = "json_schema_mode"


provider_model_to_mode = {
    ("openai", ""): Mode.JSON_SCHEMA,
    # ("openai", "*"): Mode.TOOLS,
    ("deepseek", "*"): Mode.TOOLS,
    ("openrouter", "openai/gpt-4o"): Mode.JSON_SCHEMA,
    ("openrouter", "openai/gpt-4o-mini"): Mode.JSON_SCHEMA,
    ("ollama", "*"): Mode.JSON_SCHEMA,
    ("gemini", "*"): Mode.JSON_SCHEMA,
}


class ResponseModel(Generic[T]):
    def __init__(self, func: Callable, response_model: type[T] | None = None) -> None:
        # 获取被修饰函数的返回类型
        self.response_type = self._determine_response_type(func, response_model)
        self.mode = Mode.MD_JSON
        self._validate_response_type()

    def _determine_response_type(self, func: Callable, response_model: type[T] | None) -> type[str] | type[T]:
        response_type = get_type_hints(func).get("return", str) if response_model is None else response_model
        return str if get_origin(response_type) is list or response_type is type(None) else response_type

    def _validate_response_type(self) -> None:
        if self.response_type is not str and not issubclass(self.response_type, BaseModel):
            raise TypeError(f"Unsupported return type: {self.response_type}")

    def process_parameters(
        self,
        model: str,
        messages: Messages,
        merged_api_params: dict[str, Any],
        mode: Mode | None = None,
    ) -> None:
        if self.response_type is str:
            return
        if mode is None:
            provider, model_name = model.split(":", 1)
            self.mode = next(
                (
                    mode
                    for (p, m), mode in provider_model_to_mode.items()
                    if (p == provider or p == "*") and (m == model_name or m == "*")
                ),
                Mode.MD_JSON,
            )
        else:
            self.mode = mode

        if self.mode == Mode.JSON_SCHEMA:
            self._set_response_format_from_params(merged_api_params)
        elif self.mode == Mode.TOOLS:
            self._set_tools_from_params(merged_api_params)
        elif self.mode == Mode.MD_JSON:
            self._update_markdown_json_schema_from_system_prompt(messages)

    def parse_from_response(self, choice: Any) -> str | T | ToolResponse:
        # USE TOOLS
        if hasattr(choice.message, "tool_calls") and choice.message.tool_calls and self.mode != Mode.TOOLS:
            return ToolResponse.parse(choice.message.tool_calls[0].function)
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

        except (json.JSONDecodeError, ValidationError):
            # 如果解析或验证失败，尝试使用正则表达式提取 JSON 字符串
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

    def _update_markdown_json_schema_from_system_prompt(self, messages: Messages) -> None:
        if not messages:
            raise ValueError("Messages is empty")

        system_prompt = RESPONSE_JSON_PROMPT.format(output_schema=json.dumps(self.parameters, ensure_ascii=False))
        system_message = messages[0]
        if system_message["role"] == "system":
            system_message["content"] += "\n\n" + system_prompt  # type: ignore
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
                "function": self.tool_schema,
            }
        ]
        api_params["tool_choice"] = {
            "type": "function",
            "function": {"name": self.tool_schema["name"]},
        }

    @property
    def parameters(self) -> dict[str, Any]:
        if not hasattr(self, "_parameters"):
            assert inspect.isclass(self.response_type) and issubclass(self.response_type, BaseModel)
            self._parameters: dict[str, Any] = _pydantic.to_strict_json_schema(self.response_type)
        return self._parameters

    @property
    def tool_schema(self) -> dict[str, Any]:
        if not hasattr(self, "_tool_schema"):
            self._tool_schema: dict[str, Any] = {
                "name": self.response_type.__name__,
                "description": self.response_type.__doc__ or "The final response which ends this conversation",
                "parameters": self.parameters,
                "strict": True,
            }
        return self._tool_schema
