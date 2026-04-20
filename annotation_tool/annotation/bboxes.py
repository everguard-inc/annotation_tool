from annotation_tool.annotation.figures import Figure, Point


class BBox(Figure):
    def __init__(self, x1: int, y1: int, x2: int, y2: int, label: str) -> None:
        ...

    @classmethod
    def from_points(cls, start: Point, end: Point, label: str) -> "BBox | None":
        ...
