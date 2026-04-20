import cv2
import numpy as np

from annotation_tool.annotation.figures import Figure, Point


class Mask(Figure):
    def __init__(self, label: str, mask: np.ndarray) -> None:
        self.label = label
        self.mask = mask.astype(np.uint8)
        self.selected = False
        self.active_point_id: int | None = None

    @classmethod
    def empty(cls, label: str, width: int, height: int) -> "Mask":
        return cls(label=label, mask=np.zeros((height, width), dtype=np.uint8))

    @property
    def figure_type(self) -> str:
        return "MASK"

    @property
    def surface(self) -> int:
        return int(self.mask.sum())

    def add_polygon(self, points: list[tuple[int, int]]) -> None:
        self._fill(points, value=1)

    def remove_polygon(self, points: list[tuple[int, int]]) -> None:
        self._fill(points, value=0)

    def draw(self, frame: np.ndarray, scale_factor: float, labels: dict | None = None) -> np.ndarray:
        color = labels.get(self.label, (0, 255, 255)) if labels else (0, 255, 255)
        overlay = frame.copy()
        overlay[self.mask > 0] = color
        return cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)

    def contains_point(self, point: Point) -> bool:
        if point.y < 0 or point.x < 0 or point.y >= self.mask.shape[0] or point.x >= self.mask.shape[1]:
            return False
        return bool(self.mask[point.y, point.x])

    def find_nearest_point_index(self, x: int, y: int, distance: float = 5) -> int | None:
        return None

    def move_active_point(self, x: int, y: int) -> None:
        return None

    def delete_point(self, point_id: int | None) -> None:
        self.mask[:, :] = 0

    def copy(self) -> "Mask":
        return Mask(self.label, self.mask.copy())

    def serialize(self) -> dict:
        from annotation_tool.annotation.masks_encoding import encode_rle

        return {
            "label": self.label,
            "rle": encode_rle(self.mask),
            "height": self.mask.shape[0],
            "width": self.mask.shape[1],
        }

    def _fill(self, points: list[tuple[int, int]], value: int) -> None:
        if len(points) < 3:
            return
        polygon = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(self.mask, [polygon], value)
