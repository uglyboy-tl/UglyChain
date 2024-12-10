from __future__ import annotations

from http import HTTPStatus


class BadRequestError(Exception):
    pass


class UnauthorizedError(Exception):
    pass


class RequestLimitError(Exception):
    pass


__all__ = [
    "HTTPStatus",
    "BadRequestError",
    "UnauthorizedError",
    "RequestLimitError",
]
