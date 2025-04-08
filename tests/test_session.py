from __future__ import annotations

import pytest

from uglychain.session import Session, _format_arg_str


@pytest.mark.parametrize(
    "input, expected",
    [
        ("short", "'short'"),
        ("a very long string", "'a very l...'"),
        (12345, "12345"),
        ([1, 2, 3], "[1, 2, 3..."),
        ({"key": "value"}, "{'key':..."),
    ],
)
def test_format_arg_str(input, expected):
    assert _format_arg_str(input) == expected


@pytest.mark.parametrize(
    "args, kwargs, expected",
    [
        ((1, 2), {}, "sample_func(a=1, b=2, c=3)"),
        (
            (
                1,
                {"a": 1, "b": 2},
            ),
            {"c": 2},
            "sample_func(a=1, b={'a': 1, 'b': 2}, c=2)",
        ),
        ((1,), {"b": 2}, "sample_func(a=1, b=2, c=3)"),
        (
            (
                (1, 2, 3),
                [2, 3, 4],
                {3, 4, 5},
            ),
            {},
            "sample_func(a=(1, 2,...), b=[2, 3,...], c={3, 4,...})",
        ),
    ],
)
def test_format_func_call(args, kwargs, expected):
    def sample_func(a, b, c=3):
        return a + b + c

    assert Session.format_func_call(sample_func, *args, **kwargs) == expected


def test_format_func_call_with_more_than_5_args():
    def sample_func(a, b, c, d, e, f):
        return a

    assert Session.format_func_call(sample_func, 1, 2, 3, 4, 5, 6) == "sample_func(a=1, b=2, c=3, d=4, e=5, ...)"
