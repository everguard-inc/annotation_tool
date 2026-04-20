from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, Signal


class VideoFrameProvider(QObject):
    frame_ready = Signal(int, object)
    error = Signal(str)

    def __init__(self, video_path: Path, cache_size: int = 120) -> None:
        ...

    def open(self) -> None:
        ...

    def frame_count(self) -> int:
        ...

    def request_frame(self, index: int) -> None:
        ...

    def prefetch(self, start_index: int, direction: int) -> None:
        ...

    def get_cached(self, index: int) -> np.ndarray | None:
        ...

    def close(self) -> None:
        ...
