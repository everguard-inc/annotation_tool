import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as file:
        json.dump(value, file, indent=4)
    os.replace(tmp, path)


def is_valid_json(path: Path) -> bool:
    try:
        read_json(path)
        return True
    except Exception:
        return False


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


def image_size(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as image:
        return image.size
