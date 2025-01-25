from __future__ import annotations

import time

import pytest

from uglychain.utils import retry


@pytest.mark.parametrize("n", [1, 2])
def test_retry_timeout(n):
    def sample_function():
        time.sleep(0.2)
        return "Success"

    decorated_function = retry(n=n, timeout=0.1, wait=0)(sample_function)

    with pytest.raises(Exception, match=f"Function failed after {n} attempts"):
        decorated_function()


@pytest.mark.parametrize("n", [1, 3])
def test_retry_exception(n):
    def sample_function():
        raise ValueError("Test error")

    decorated_function = retry(n=n, timeout=1, wait=0.1)(sample_function)

    with pytest.raises(Exception, match=f"Function failed after {n} attempts"):
        decorated_function()


def test_retry_success():
    def sample_function():
        return "Success"

    decorated_function = retry(n=3, timeout=1, wait=1)(sample_function)

    result = decorated_function()
    assert result == "Success"
