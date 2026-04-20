import numpy as np

from annotation_tool.annotation.figures import Figure


class Mask(Figure):
    def __init__(self, label: str, mask: np.ndarray) -> None:
        ...

    @classmethod
    def empty(cls, label: str, width: int, height: int) -> "Mask":
        ...

    def add_polygon(self, points: list[tuple[int, int]]) -> None:
        ...

    def remove_polygon(self, points: list[tuple[int, int]]) -> None:
        ...
