from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from functools import wraps
from typing import Any, ParamSpec

P = ParamSpec("P")


class RetryError(Exception):
    def __init__(self, message: str, errors: list[Exception]) -> None:
        super().__init__(message)
        self.errors = errors

    def __str__(self) -> str:
        error_messages = "\n".join([str(error) for error in self.errors])
        return f"{self.args[0]}\nPrevious errors:\n{error_messages}"


def retry(
    n: int, timeout: float, wait: float, executor: ThreadPoolExecutor | None = None
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    def decorator_retry(func: Callable[P, Any]) -> Callable[P, Any]:
        max_retries = n
        llm_timeout = timeout

        @wraps(func)
        def wrapper_retry(*args: P.args, **kwargs: P.kwargs) -> Any:
            attempts = 0
            errors: list[Exception] = []
            nonlocal executor
            if executor is None:
                executor = ThreadPoolExecutor()
            while attempts < max_retries:
                future = executor.submit(func, *args, **kwargs)
                try:
                    result = future.result(timeout=llm_timeout)
                    return result
                except TimeoutError as e:
                    print(
                        f"Function execution exceeded {llm_timeout} seconds, retrying... (attempt {attempts + 1}/{max_retries})"
                    )
                    errors.append(e)
                    attempts += 1
                except Exception as e:
                    print(
                        f"Function {func.__name__} failed with error: {e}, retrying... (attempt {attempts + 1}/{max_retries})"
                    )
                    errors.append(e)
                    attempts += 1
                if wait > 0:
                    time.sleep(wait)
            raise RetryError(f"Function {func.__name__} failed after {n} attempts", errors)

        return wrapper_retry

    return decorator_retry
