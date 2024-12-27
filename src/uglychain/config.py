from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Config(BaseModel):
    default_api_params: dict[str, Any] = Field(
        default_factory=dict, description="Default parameters for language models."
    )
    use_parallel_processing: bool = Field(
        default=False, description="Whether to use parallel processing for language models."
    )

    def __init__(self, **data):
        super().__init__(**data)


config = Config()
