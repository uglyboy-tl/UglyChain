#!/usr/bin/env python3

from dataclasses import dataclass

from loguru import logger
from pydantic import BaseModel, Field

from uglychain import LLM
from uglychain.storage import FileStorage

from .base import BaseWorker


class CodeType(BaseModel):
    reason: str = Field(..., description="your thought process and solution")
    code: str = Field(..., description="the final code in the optimized file")


@dataclass
class Developer(BaseWorker):
    prompt: str = "{context}"
    role: str = ""
    name: str = ""
    file_path: str = "data/code/test.py"

    def __post_init__(self):
        self.llm = LLM(
            self.prompt,
            self.model,
            self.role,
            CodeType,
        )
        if not self.storage:
            self.storage = FileStorage(self.file_path)

    def run(self, *args, **kwargs):
        logger.info(f"正在执行 {self.name} 的任务...")
        response = self._ask(*args, **kwargs)
        logger.success(response.reason)
        if self.storage:
            self.storage.save(response.code)
        return response.code
