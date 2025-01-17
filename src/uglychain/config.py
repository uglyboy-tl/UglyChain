from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Config(BaseModel):
    default_model: str = Field(default="openai:gpt-4o-mini", description="默认语言模型。")
    default_api_params: dict[str, Any] = Field(default_factory=dict, description="语言模型的默认参数。")
    use_parallel_processing: bool = Field(default=False, description="是否对语言模型使用并行处理。")
    verbose: bool = Field(default=False, description="如果为真，则启用详细日志记录。")
    need_confirm: bool = Field(default=False, description="如果为真，则工具使用需要确认。")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)


config = Config()
