import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .base import Storage


@dataclass
class SQLiteStorage(Storage):
    file: str = "data/cache.db"
    table: str = "cache"
    expirationIntervalInDays: int = 10

    def __post_init__(self):
        path = Path(self.file)
        with sqlite3.connect(path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} (key TEXT PRIMARY KEY, value TEXT, timestamp TEXT Not NULL DEFAULT (date('now','localtime')))"
            )
        self._conn = sqlite3.connect(path)
        self._cur = self._conn.cursor()

    def save(self, data: Dict[str, str]):
        self._cur.executemany(
            f"""
            INSERT OR REPLACE INTO {self.table} (key, value)
            VALUES (?, ?)
        """,
            data.items(),
        )
        self._conn.commit()

    def load(self, keys: List[str] | str | None, condition: str | None = None) -> Dict[str, str]:
        if keys is None:
            query_sql = (
                f"SELECT key, value FROM {self.table} WHERE date('now', 'localtime') < date(timestamp, '+? day')"
            )
            if condition is not None:
                query_sql += f" and {condition}"
            self._cur.execute(query_sql, (self.expirationIntervalInDays,))
            return {row[0]: row[1] for row in self._cur.fetchall()}
        if isinstance(keys, str):
            keys = [keys]

        placeholders = ", ".join("?" for _ in keys)
        params = keys + [str(self.expirationIntervalInDays)]
        query_sql = f"SELECT key, value FROM {self.table} WHERE key IN ({placeholders}) and date('now', 'localtime') < date(timestamp, '+' || ? || ' day')"
        if condition is not None:
            query_sql += f" and {condition}"
        self._cur.execute(query_sql, params)

        return {row[0]: row[1] for row in self._cur.fetchall()}
