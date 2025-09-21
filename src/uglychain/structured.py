"""
structured模块提供结构化输出处理功能。

该模块实现了从LLM响应中解析结构化数据的功能，支持多种输出模式：
- JSON Schema模式：使用OpenAI的JSON Schema功能
- 工具调用模式：使用OpenAI的Function Calling功能
- Markdown模式：通过系统提示引导LLM生成特定格式的输出
"""

from __future__ import annotations

import inspect  # 用于检查类和函数
import json  # 用于JSON处理
import re  # 用于正则表达式匹配
from collections.abc import Callable  # 用于类型提示
from enum import Enum, unique  # 用于枚举类型
from functools import cached_property  # 用于属性缓存
from typing import Any, Generic, get_origin, get_type_hints  # 用于类型处理

from openai.lib import _pydantic  # 用于OpenAI的Pydantic集成
from pydantic import BaseModel, ValidationError  # 用于数据验证
from ruamel.yaml import YAML, YAMLError  # 用于YAML处理

from .config import config  # 导入配置
from .prompt import RESPONSE_JSON_PROMPT, RESPONSE_YAML_PROMPT  # 导入提示模板
from .schema import Messages, T, ToolResponse  # 导入类型定义

# 常量定义
YAML_INSTANCE = YAML()  # 创建YAML实例
YAML_INSTANCE.preserve_quotes = True  # 保留引号


@unique
class Mode(Enum):
    """
    响应处理模式枚举。

    定义了三种不同的响应处理模式：
    - TOOLS: 使用工具调用（Function Calling）
    - MARKDOWN: 使用Markdown格式提示
    - JSON_SCHEMA: 使用JSON Schema格式
    """

    TOOLS = "tool_call"  # 工具调用模式
    MARKDOWN = "markdown_mode"  # Markdown模式
    JSON_SCHEMA = "json_schema_mode"  # JSON Schema模式


# 提供商和模型到模式的映射
provider_model_to_mode = {
    ("openai", ""): Mode.JSON_SCHEMA,  # OpenAI默认使用JSON Schema
    # ("openai", "*"): Mode.TOOLS,  # 注释掉的配置
    ("deepseek", "*"): Mode.TOOLS,  # Deepseek使用工具调用
    ("openrouter", "openai/gpt-4o"): Mode.JSON_SCHEMA,  # OpenRouter的GPT-4o使用JSON Schema
    ("openrouter", "openai/gpt-4o-mini"): Mode.JSON_SCHEMA,  # OpenRouter的GPT-4o-mini使用JSON Schema
    ("ollama", "*"): Mode.JSON_SCHEMA,  # Ollama使用JSON Schema
    ("gemini", "*"): Mode.JSON_SCHEMA,  # Gemini使用JSON Schema
}


class ResponseModel(Generic[T]):
    """
    响应模型处理类，用于处理和解析LLM的结构化输出。

    支持多种输出模式和格式，能够将LLM的文本响应转换为结构化的Python对象。
    """

    def __init__(self, func: Callable, response_model: type[T] | None = None) -> None:
        """
        初始化响应模型处理器。

        Args:
            func: 被装饰的函数
            response_model: 可选的响应模型类型，如果未提供则从函数返回类型推断
        """
        # 初始化模式和类型
        self.mode = Mode.MARKDOWN  # 默认使用Markdown模式
        self.type = config.response_markdown_type  # 从配置获取Markdown类型（json或yaml）
        self.response_type = self._determine_response_type(func, response_model)  # 确定响应类型
        self._validate_response_type()  # 验证响应类型

    def _determine_response_type(self, func: Callable, response_model: type[T] | None) -> type[str] | type[T]:
        """
        确定响应类型。

        Args:
            func: 被装饰的函数
            response_model: 可选的响应模型类型

        Returns:
            确定的响应类型
        """
        response_type = get_type_hints(func).get("return", str) if response_model is None else response_model
        return str if get_origin(response_type) is list or response_type is type(None) else response_type

    def _validate_response_type(self) -> None:
        """
        验证响应类型是否支持。

        Raises:
            TypeError: 如果响应类型不是str或BaseModel的子类
        """
        if self.response_type is not str and not issubclass(self.response_type, BaseModel):
            raise TypeError(f"Unsupported return type: {self.response_type}")

    def process_parameters(
        self,
        model: str,
        messages: Messages,
        merged_api_params: dict[str, Any],
        mode: Mode | None = None,
    ) -> None:
        """
        处理API参数，根据模式设置适当的参数。

        Args:
            model: 模型标识符（格式：provider:model_name）
            messages: 消息列表
            merged_api_params: 合并后的API参数
            mode: 可选的模式覆盖
        """
        # 如果响应类型是字符串，不需要特殊处理
        if self.response_type is str:
            return

        # 确定处理模式
        if mode is None:
            provider, model_name = model.split(":", 1)
            # 根据提供商和模型名称查找匹配的模式
            self.mode = next(
                (
                    mode
                    for (p, m), mode in provider_model_to_mode.items()
                    if (p == provider or p == "*") and (m == model_name or m == "*")
                ),
                Mode.MARKDOWN,  # 默认使用Markdown模式
            )
        else:
            self.mode = mode

        # 根据模式设置参数
        if self.mode == Mode.JSON_SCHEMA:
            self._set_response_format_from_params(merged_api_params)
        elif self.mode == Mode.TOOLS:
            self._set_tools_from_params(merged_api_params)
        elif self.mode == Mode.MARKDOWN:
            self._update_markdown_json_schema_from_system_prompt(messages)

    def parse_from_response(self, choice: Any) -> str | T | ToolResponse:
        """
        从LLM响应中解析结构化数据。

        Args:
            choice: LLM响应的选择对象

        Returns:
            解析后的结构化数据，可能是字符串、工具响应或模型实例

        Raises:
            ValueError: 如果解析失败
        """
        reasoning_content: str = ""
        # 处理推理内容（如果有）
        if hasattr(choice.message, "reasoning_content"):
            reasoning_content = choice.message.reasoning_content

        # 处理工具调用
        if hasattr(choice.message, "tool_calls") and choice.message.tool_calls and self.mode != Mode.TOOLS:
            return ToolResponse.parse(choice.message.tool_calls[0].function)

        # 处理字符串响应类型
        if self.response_type is str:
            response = f"<thinking>\n{reasoning_content}\n</thinking>\n" if reasoning_content else ""
            response += choice.message.content.strip()
            return response

        # 验证响应类型
        assert issubclass(self.response_type, BaseModel) and not inspect.isabstract(self.response_type)

        # 根据模式获取响应内容
        if self.mode == Mode.MARKDOWN or self.mode == Mode.JSON_SCHEMA:
            response = choice.message.content.strip()
        elif self.mode == Mode.TOOLS:
            response = choice.message.tool_calls[0].function.arguments
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

        # 根据类型解析响应
        if self.type == "yaml":
            try:
                # 尝试从YAML格式解析
                match = re.search(r"```yaml\s*\n(.*?)(```|$)", response.strip(), re.IGNORECASE | re.DOTALL)
                yaml_str = response.strip()
                if yaml_str.endswith("```"):
                    yaml_str = yaml_str[:-3]
                if match:
                    yaml_str = match.group(1).strip()
                yaml_obj = YAML_INSTANCE.load(yaml_str)
                return self.response_type.model_validate_json(json.dumps(yaml_obj))  # type: ignore[union-attr]

            except (YAMLError, ValidationError) as e:
                # 解析失败时抛出异常
                name = self.response_type.__name__
                msg = f"Failed to parse {name} from completion {response}. Got: {e}"
                raise ValueError(msg) from e
        else:
            try:
                # 尝试直接解析JSON
                json.loads(response.strip())
                return self.response_type.model_validate_json(response.strip())  # type: ignore[union-attr]

            except (json.JSONDecodeError, ValidationError):
                # 如果直接解析失败，尝试使用正则表达式提取JSON
                match = re.search(r"(\{.*\})", response.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
                if match:
                    json_str = match.group()
                    try:
                        return self.response_type.model_validate_json(json_str)  # type: ignore[union-attr]
                    except (json.JSONDecodeError, ValidationError) as e:
                        # 解析失败时抛出异常
                        name = self.response_type.__name__
                        msg = f"Failed to parse {name} from completion {response}. Got: {e}"
                        raise ValueError(msg) from e
                else:
                    # 未找到JSON对象时抛出异常
                    name = self.response_type.__name__
                    raise ValueError(f"Failed to find JSON object in response for {name}: {response}") from None

    def _update_markdown_json_schema_from_system_prompt(self, messages: Messages) -> None:
        """
        更新系统提示，添加JSON Schema或YAML格式指导。

        Args:
            messages: 消息列表

        Raises:
            ValueError: 如果消息列表为空
        """
        if not messages:
            raise ValueError("Messages is empty")

        # 根据类型选择提示模板
        if self.type == "yaml":
            system_prompt = RESPONSE_YAML_PROMPT.format(output_schema=json.dumps(self.parameters, ensure_ascii=False))
        else:
            system_prompt = RESPONSE_JSON_PROMPT.format(output_schema=json.dumps(self.parameters, ensure_ascii=False))

        # 更新或添加系统消息
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
        """
        设置JSON Schema响应格式参数。

        Args:
            api_params: API参数字典
        """
        api_params["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": self.response_type.__name__,
                "schema": self.parameters,
                "strict": True,
            },
        }

    def _set_tools_from_params(self, api_params: dict[str, Any]) -> None:
        """
        设置工具调用参数。

        Args:
            api_params: API参数字典
        """
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

    @cached_property
    def parameters(self) -> dict[str, Any]:
        """
        获取响应类型的JSON Schema参数。

        Returns:
            JSON Schema参数字典
        """
        if not issubclass(self.response_type, BaseModel):
            return {}
        return _pydantic.to_strict_json_schema(self.response_type)

    @cached_property
    def tool_schema(self) -> dict[str, Any]:
        """
        获取工具调用的Schema。

        Returns:
            工具Schema字典
        """
        return {
            "name": self.response_type.__name__,
            "description": self.response_type.__doc__ or "The final response which ends this conversation",
            "parameters": self.parameters,
            "strict": True,
        }
