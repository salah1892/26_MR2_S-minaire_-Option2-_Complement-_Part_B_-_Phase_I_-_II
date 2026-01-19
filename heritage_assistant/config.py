from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"


def get_paths() -> Paths:
    # This file lives in heritage_assistant/, so project root is its parent.
    root = Path(__file__).resolve().parent.parent
    return Paths(root=root)
