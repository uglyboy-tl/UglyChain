#!/usr/bin/env python3
from __future__ import annotations

import threading
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class _SingletonWrapper(Generic[T]):
    """A singleton wrapper class.

    Instances of this class are created for each decorated class.
    """

    def __init__(self, cls: type[T]):
        self.__wrapped__ = cls
        self._instance: T | None = None
        self._lock = threading.Lock()

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        """Returns a single instance of the decorated class"""
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = self.__wrapped__(*args, **kwargs)
        return self._instance


def singleton(cls: type[T]) -> type[T]:
    """A singleton decorator.

    Returns a wrapper object. A call on that object returns a single instance
    object of the decorated class. Use the __wrapped__ attribute to access the
    decorated class directly in unit tests.
    """
    if not hasattr(cls, "__new__") or not callable(cls.__new__):
        raise TypeError("Cannot decorate a class that cannot be instantiated")
    return _SingletonWrapper(cls)  # type: ignore
