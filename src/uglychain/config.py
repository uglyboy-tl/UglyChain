from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Config(BaseModel):
    default_model: str = Field(default="openai:gpt-4o-mini", description="默认语言模型。")
    default_api_params: dict[str, Any] = Field(default_factory=dict, description="语言模型的默认参数。")
    default_language: str = Field(default="Chinese", description="默认语言。")
    response_markdown_type: str = Field(default="yaml", description="默认的markdown类型。")
    llm_max_retry: int = Field(default=3, description="语言模型的最大重试次数。")
    llm_timeout: int = Field(default=30, description="语言模型的最大运行时间（秒）。")
    llm_wait_time: int = Field(default=0, description="语言模型的每次重试等待时间（秒）。")
    use_parallel_processing: bool = Field(default=False, description="是否对语言模型使用并行处理。")
    verbose: bool = Field(default=False, description="如果为真，则启用详细日志记录。")
    need_confirm: bool = Field(default=False, description="如果为真，则工具使用需要确认。")


config = Config()
