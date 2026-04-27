from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal

from annotation_tool.media.frame_cache import FrameCache


class VideoFrameProvider(QObject):
    frame_ready = Signal(int, object)
    error = Signal(str)

    def __init__(self, video_path: Path, cache_size: int = 180) -> None:
        super().__init__()
        self.video_path = video_path
        self.cache = FrameCache(cache_size)
        self.capture: cv2.VideoCapture | None = None
        self._frame_count = 0
        self._next_capture_index = 0

    def open(self) -> None:
        self.capture = cv2.VideoCapture(str(self.video_path))
        if not self.capture.isOpened():
            raise RuntimeError(f"Unable to open video: {self.video_path}")

        self._frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self._next_capture_index = 0

    def frame_count(self) -> int:
        return self._frame_count

    def request_frame(self, index: int) -> np.ndarray:
        index = self._normalize_index(index)

        cached = self.cache.get(index)
        if cached is not None:
            self.frame_ready.emit(index, cached)
            return cached

        frame = self._read_frame(index)
        self.cache.put(index, frame)
        self.frame_ready.emit(index, frame)
        return frame

    def prefetch(self, start_index: int, direction: int) -> None:
        if direction == 0 or self._frame_count <= 0:
            return
        target = self._normalize_index(start_index + direction)
        if target == start_index:
            return
        if self.cache.get(target) is not None:
            return
        frame = self._read_frame(target)
        self.cache.put(target, frame)

    def get_cached(self, index: int) -> np.ndarray | None:
        return self.cache.get(index)

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None

        self.cache.clear()
        self._next_capture_index = 0

    def _read_frame(self, index: int) -> np.ndarray:
        if self.capture is None:
            raise RuntimeError("Video provider is not opened.")

        if index != self._next_capture_index:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            self._next_capture_index = index

        ok, frame = self.capture.read()
        if not ok or frame is None:
            raise RuntimeError(f"Unable to read video frame {index}")

        self._next_capture_index = index + 1
        return frame

    def _normalize_index(self, index: int) -> int:
        if self._frame_count <= 0:
            return 0
        return max(0, min(index, self._frame_count - 1))
