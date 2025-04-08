from __future__ import annotations

from ..core import Tool


@Tool.tool
def final_answer(answer: str) -> str:
    """When get Final Answer, use this tool to return the answer and finishes the task."""
    return answer
