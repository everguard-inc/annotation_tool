from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AppSettings:
    token: str
    api_url: str
    file_url: str
    data_dir: Path
    bbox_line_width: float
    cursor_proximity_threshold: float
    objects_opacity: float
    color_fill_opacity: float
    bbox_handler_size: float
    keypoint_handler_size: float


class SettingsStore:
    def __init__(self, path: Path) -> None:
        ...

    def load(self) -> AppSettings:
        ...

    def save(self, settings: AppSettings) -> None:
        ...

    def raw(self) -> dict[str, Any]:
        ...
