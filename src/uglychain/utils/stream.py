from __future__ import annotations

import threading
from collections.abc import Generator, Iterator
from typing import Any


class Stream:
    def __init__(self, source_iterator: Iterator[str]):
        self._source = source_iterator
        self._cache: list[str] = []  # 存储所有接收到的数据
        self._lock = threading.Lock()  # 保护共享资源的锁
        self._stopped = False  # 标记源迭代器是否耗尽

        # 启动后台线程持续消费源迭代器
        self._thread = threading.Thread(target=self._consume_source)
        self._thread.daemon = True  # 设为守护线程避免程序无法退出
        self._thread.start()

    def _consume_source(self) -> None:
        """后台线程任务：持续消费源迭代器并填充缓存"""
        for item in self._source:
            with self._lock:
                self._cache.append(item)

        # 源迭代器耗尽后标记停止
        with self._lock:
            self._stopped = True

    @property
    def iterator(self) -> Generator[str, None, None]:
        """生成一个从当前缓存位置开始的新迭代器"""
        current_index = 0

        while True:
            if current_index < len(self._cache):
                item = self._cache[current_index]
                current_index += 1
                yield item
                continue

            if self._stopped and current_index >= len(self._cache):
                break
