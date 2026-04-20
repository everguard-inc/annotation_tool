import numpy as np


class FrameCache:
    def __init__(self, max_size: int) -> None:
        ...

    def get(self, index: int) -> np.ndarray | None:
        ...

    def put(self, index: int, frame: np.ndarray) -> None:
        ...

    def clear(self) -> None:
        ...

    def contains(self, index: int) -> bool:
        ...
