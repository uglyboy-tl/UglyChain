from __future__ import annotations

import time

import pytest

from uglychain.utils.retry import RetryError, retry


@pytest.mark.parametrize(
    "n, timeout, wait, exception, match",
    [
        (1, 0.1, 0, RetryError, "Function sample_function failed after 1 attempts"),
        (2, 0.1, 0, RetryError, "Function sample_function failed after 2 attempts"),
        (1, 1, 0.1, RetryError, "Function sample_function failed after 1 attempts"),
        (3, 1, 0.1, RetryError, "Function sample_function failed after 3 attempts"),
    ],
)
def test_retry(n, timeout, wait, exception, match):
    def sample_function():
        if timeout == 0.1:
            time.sleep(0.2)
        else:
            raise ValueError("Test error")

    decorated_function = retry(n=n, timeout=timeout, wait=wait)(sample_function)

    with pytest.raises(exception, match=match):
        decorated_function()


@pytest.mark.parametrize(
    "n, timeout, wait, expected",
    [
        (3, 1, 1, "Success"),
    ],
)
def test_retry_success(n, timeout, wait, expected):
    def sample_function():
        return "Success"

    decorated_function = retry(n=n, timeout=timeout, wait=wait)(sample_function)

    result = decorated_function()
    assert result == expected
