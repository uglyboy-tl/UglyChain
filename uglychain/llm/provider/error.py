from http import HTTPStatus


class BadRequestError(Exception):
    pass


class Unauthorized(Exception):
    pass


class RequestLimitError(Exception):
    pass


__all__ = [
    "HTTPStatus",
    "BadRequestError",
    "Unauthorized",
    "RequestLimitError",
]
