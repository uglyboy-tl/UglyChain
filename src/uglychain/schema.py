"""
schema模块定义了UglyChain框架中使用的核心数据类型和模型。
包括类型参数、消息格式和工具响应模型。
"""

from __future__ import annotations

import json  # 导入json模块，用于解析JSON字符串
from collections.abc import Callable  # 导入Callable类型，用于类型提示
from typing import Any, ParamSpec, TypeVar  # 导入类型提示工具

from pydantic import BaseModel, Field  # 导入Pydantic模型和字段

# 类型参数定义
P = ParamSpec("P")  # 参数规格，用于泛型函数
T = TypeVar("T", bound=BaseModel)  # 类型变量，限定为BaseModel的子类
Content = TypeVar("Content", bound=str | dict[str, Any])  # 内容类型变量，可以是字符串或字典
Messages = list[dict[str, Content]]  # 消息类型，表示消息列表


class ToolResponse(BaseModel):
    """
    工具响应模型，用于表示LLM调用工具的响应。

    包含工具名称和参数，并提供解析和执行工具的方法。
    """

    name: str = Field(..., description="tool name")  # 工具名称
    parameters: dict = Field(..., description="tool arguments")  # 工具参数

    @classmethod
    def parse(cls, response: Any) -> ToolResponse:
        """
        从LLM响应解析工具调用。

        Args:
            response: LLM返回的工具调用响应

        Returns:
            ToolResponse: 解析后的工具响应对象
        """
        return cls(name=response.name, parameters=json.loads(response.arguments))

    def run_function(self, tools: list[Callable[..., str]]) -> str:
        """
        执行与工具名称匹配的函数。

        Args:
            tools: 可用工具函数列表

        Returns:
            str: 工具执行的结果

        Raises:
            ValueError: 如果找不到匹配的工具
        """
        for tool in tools:
            if tool.__name__ == self.name:
                return tool(**self.parameters)
        raise ValueError(f"Can't find tool {self.name}")
