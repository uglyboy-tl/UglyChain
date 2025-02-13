from __future__ import annotations

import pytest

from uglychain.utils.singleton import singleton


# Dummy class to test singleton behavior
@singleton
class SingletonClass:
    def __init__(self, value):
        self.value = value


def test_singleton_instance():
    instance1 = SingletonClass(10)
    instance2 = SingletonClass(20)

    assert instance1 is instance2
    assert instance1.value == 10
    assert instance2.value == 10


def test_singleton_thread_safety():
    import threading

    instances = []

    def instantiate_singleton():
        instance = SingletonClass(30)
        instances.append(instance)

    threads = [threading.Thread(target=instantiate_singleton) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Ensure all instances are the same
    assert all(instance is instances[0] for instance in instances)


def test_decorator_type_error():
    with pytest.raises(TypeError, match="Cannot decorate a class that cannot be instantiated"):

        class NoNewMeta:
            __new__ = None  # type: ignore

        @singleton
        class NonInstantiable(NoNewMeta):
            def __init__(self):
                pass
