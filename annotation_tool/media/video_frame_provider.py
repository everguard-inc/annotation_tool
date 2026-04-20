from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal

from annotation_tool.media.frame_cache import FrameCache


class VideoFrameProvider(QObject):
    frame_ready = Signal(int, object)
    error = Signal(str)

    def __init__(self, video_path: Path, cache_size: int = 120) -> None:
        super().__init__()
        self.video_path = video_path
        self.cache = FrameCache(cache_size)
        self.capture: cv2.VideoCapture | None = None
        self._frame_count = 0

    def open(self) -> None:
        self.capture = cv2.VideoCapture(str(self.video_path))
        if not self.capture.isOpened():
            raise RuntimeError(f"Unable to open video: {self.video_path}")

        self._frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

    def frame_count(self) -> int:
        return self._frame_count

    def request_frame(self, index: int) -> np.ndarray:
        cached = self.cache.get(index)
        if cached is not None:
            self.frame_ready.emit(index, cached)
            return cached

        frame = self._read_frame(index)
        self.cache.put(index, frame)
        self.frame_ready.emit(index, frame)
        return frame

    def prefetch(self, start_index: int, direction: int) -> None:
        if self.capture is None:
            return

        for offset in range(1, min(self.cache.max_size, 30)):
            index = start_index + offset * direction
            if index < 0 or index >= self._frame_count:
                break

            if not self.cache.contains(index):
                self.cache.put(index, self._read_frame(index))

    def get_cached(self, index: int) -> np.ndarray | None:
        return self.cache.get(index)

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        self.cache.clear()

    def _read_frame(self, index: int) -> np.ndarray:
        if self.capture is None:
            raise RuntimeError("Video provider is not opened.")

        index = max(0, min(index, self._frame_count - 1))
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, index)

        ok, frame = self.capture.read()
        if not ok or frame is None:
            raise RuntimeError(f"Unable to read video frame {index}")

        return frame
