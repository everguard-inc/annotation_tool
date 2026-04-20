from collections import OrderedDict

import numpy as np


class FrameCache:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size
        self._items: OrderedDict[int, np.ndarray] = OrderedDict()

    def get(self, index: int) -> np.ndarray | None:
        frame = self._items.get(index)
        if frame is not None:
            self._items.move_to_end(index)
        return frame

    def put(self, index: int, frame: np.ndarray) -> None:
        self._items[index] = frame
        self._items.move_to_end(index)

        while len(self._items) > self.max_size:
            self._items.popitem(last=False)

    def clear(self) -> None:
        self._items.clear()

    def contains(self, index: int) -> bool:
        return index in self._items
