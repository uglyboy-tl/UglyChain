from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class BaseTool:
    name: str
    description: str
    args_schema: dict[str, Any]


def get_tools_descriptions(tools: list[BaseTool]) -> str:
    descriptions = []
    for tool in tools:
        markdown = f"### {tool.name}\n"
        markdown += f"> {tool.description}\n\n"
        markdown += f"{json.dumps(tool.args_schema, ensure_ascii=False)}\n"
        descriptions.append(markdown)
    return "\n".join(descriptions)
