from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    ...


def write_json(path: Path, value: Any) -> None:
    ...


def is_valid_json(path: Path) -> bool:
    ...


def now_string() -> str:
    ...


def image_size(path: Path) -> tuple[int, int]:
    ...
