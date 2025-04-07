from __future__ import annotations

from typing import Any

from uglychain.schema import T
from uglychain.session import Session
from uglychain.tools import BaseTool

from .base import BaseReActProcess
from .default import ReActProcess


def get_react_process(
    model: str, session: Session, tools: list[BaseTool], response_format: type[T] | None, api_params: dict[str, Any]
) -> BaseReActProcess:
    return ReActProcess(model, session, tools, response_format, api_params)
