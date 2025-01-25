from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from functools import wraps
from typing import Any, ParamSpec

P = ParamSpec("P")


def retry(n: int, timeout: float, wait: float) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    def decorator_retry(func: Callable[P, Any]) -> Callable[P, Any]:
        max_retries = n
        llm_timeout = timeout

        @wraps(func)
        def wrapper_retry(*args: P.args, **kwargs: P.kwargs) -> Callable[P, Any]:
            attempts = 0
            while attempts < max_retries:
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(func, *args, **kwargs)
                    try:
                        result = future.result(timeout=llm_timeout)
                        return result
                    except TimeoutError:
                        print(f"Function execution exceeded {llm_timeout} seconds, retrying...")
                        attempts += 1
                    except Exception as e:
                        print(f"Function failed with error: {e}, retrying...")
                        attempts += 1
                if wait > 0:
                    time.sleep(wait)
            raise Exception(f"Function failed after {n} attempts")

        return wrapper_retry

    return decorator_retry
