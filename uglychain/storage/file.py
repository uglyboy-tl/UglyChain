from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from shutil import copy2

from loguru import logger

from .base import Storage


class FileNotFoundInWorkspaceError(Exception):
    pass


@dataclass
class FileStorage(Storage):
    file: str = "data/temp"
    path: Path = field(init=False)

    def __post_init__(self):
        self.path = Path(self.file)

    def save(self, data: str):
        # self.path.write_text(data)
        if self.path.exists():
            self._backup(self.path)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(data)
        logger.debug(f"保存文件至 `{self.path}`")

    def load(self) -> str:
        if not self.path.exists():
            raise FileNotFoundInWorkspaceError(f"File {self.file} not found in workspace.")
        return self.path.read_text()

    @classmethod
    def _backup(cls, file_path: Path):
        backup_path = file_path.with_suffix(file_path.suffix + "." + datetime.now().strftime("%Y%m%d%H%M%S") + ".bak")
        copy2(file_path, backup_path)
