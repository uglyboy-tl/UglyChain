from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dill

from .base import Storage


@dataclass
class DillStorage(Storage):
    file: str = "data/temp.pkl"

    def __post_init__(self):
        self.path = Path(self.file)

    def save(self, data: Any):
        with open(self.path, "wb") as f:
            dill.dump(data, f)

    def load(self) -> Any:
        with open(self.path, "rb") as f:
            return dill.load(f)
