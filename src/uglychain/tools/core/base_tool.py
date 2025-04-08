from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BaseTool:
    name: str
    description: str
    args_schema: dict[str, Any]
