import cv2
import numpy as np

from annotation_tool.annotation.figures import AnnotationStyle, Figure, Point


class ReviewLabel(Figure):
    def __init__(self, x: int, y: int, label: str) -> None:
        self.x = x
        self.y = y
        self.label = label
        self.selected = False
        self.active_point_id: int | None = None

    @property
    def figure_type(self) -> str:
        return "REVIEW_LABEL"

    @property
    def surface(self) -> int:
        return 1

    def draw(
        self,
        frame: np.ndarray,
        scale_factor: float,
        labels: dict | None = None,
        style: AnnotationStyle | None = None,
    ) -> np.ndarray:
        color = labels.get(self.label, (0, 255, 255)) if labels else (0, 255, 255)
        cv2.circle(frame, (self.x, self.y), 5, color, -1)
        cv2.line(frame, (self.x, self.y), (self.x + 30, self.y - 30), (255, 255, 255), 2)
        cv2.putText(frame, self.label, (self.x + 35, self.y - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        return frame

    def contains_point(self, point: Point) -> bool:
        return False

    def find_nearest_point_index(self, x: int, y: int, distance: float = 15) -> int | None:
        return 0 if Point(self.x, self.y).close_to(x, y, distance) else None

    def move_active_point(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def delete_point(self, point_id: int | None) -> None:
        self.x = self.y = -1

    def copy(self) -> "ReviewLabel":
        return ReviewLabel(self.x, self.y, self.label)

    def serialize(self) -> dict:
        return {"x": self.x, "y": self.y, "label": self.label}
