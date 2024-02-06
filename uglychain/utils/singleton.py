#!/usr/bin/env python3


class _SingletonWrapper:
    """A singleton wrapper class.

    Instances of this class are created for each decorated class.
    """

    def __init__(self, cls):
        self.__wrapped__ = cls
        self._instance = None

    def __call__(self, *args, **kwargs):
        """Returns a single instance of the decorated class"""
        if self._instance is None:
            self._instance = self.__wrapped__(*args, **kwargs)
        return self._instance


def singleton(cls):
    """A singleton decorator.

    Returns a wrapper object. A call on that object returns a single instance
    object of the decorated class. Use the __wrapped__ attribute to access the
    decorated class directly in unit tests.
    """
    return _SingletonWrapper(cls)
