import cv2
import numpy as np

from annotation_tool.annotation.figures import AnnotationStyle, Figure, Point


class BBox(Figure):
    def __init__(self, x1: int, y1: int, x2: int, y2: int, label: str) -> None:
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
        self.label = label
        self.selected = False
        self.active_point_id: int | None = None
        self.show_label = False
        self.show_size = False

    @classmethod
    def from_points(cls, start: Point, end: Point, label: str) -> "BBox | None":
        if abs(start.x - end.x) < 3 or abs(start.y - end.y) < 3:
            return None
        return cls(start.x, start.y, end.x, end.y, label)

    @property
    def figure_type(self) -> str:
        return "BBOX"

    @property
    def surface(self) -> int:
        return abs(self.x2 - self.x1) * abs(self.y2 - self.y1)

    @property
    def points(self) -> list[Point]:
        return [
            Point(self.x1, self.y1),
            Point(self.x2, self.y1),
            Point(self.x2, self.y2),
            Point(self.x1, self.y2),
        ]

    def draw(
        self,
        frame: np.ndarray,
        scale_factor: float,
        labels: dict | None = None,
        style: AnnotationStyle | None = None,
    ) -> np.ndarray:
        style = style or AnnotationStyle()
        color = self._color(labels)
        line_width = max(1, int(style.bbox_line_width / max(scale_factor, 1) ** 0.33))

        if self.selected:
            line_width += 1

        if style.color_fill_opacity > 0:
            original = frame.copy()
            cv2.rectangle(frame, (self.x1, self.y1), (self.x2, self.y2), color, -1)
            frame = cv2.addWeighted(
                frame,
                style.color_fill_opacity,
                original,
                max(1 - style.color_fill_opacity, 0),
                0,
            )

        cv2.rectangle(frame, (self.x1, self.y1), (self.x2, self.y2), color, line_width)

        text_parts = []
        if self.show_label:
            text_parts.append(self.label)
        if self.show_size:
            text_parts.append(f"{abs(self.y2 - self.y1)}x{abs(self.x2 - self.x1)}")

        if text_parts:
            cv2.putText(
                frame,
                ", ".join(text_parts),
                (self.x1, max(15, self.y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        if self.selected:
            radius = max(1, int(style.bbox_handler_size / max(scale_factor, 1) ** 0.33))
            for point in self.points:
                cv2.circle(frame, (point.x, point.y), radius, (255, 255, 255), -1)
                cv2.circle(frame, (point.x, point.y), radius, (0, 0, 0), 1)

        return frame

    def contains_point(self, point: Point) -> bool:
        return self.x1 <= point.x <= self.x2 and self.y1 <= point.y <= self.y2

    def find_nearest_point_index(self, x: int, y: int, distance: float = 5) -> int | None:
        for index, point in enumerate(self.points):
            if point.close_to(x, y, distance):
                return index
        return None

    def move_active_point(self, x: int, y: int) -> None:
        if self.active_point_id is None:
            return

        opposite = self.points[(self.active_point_id + 2) % 4]
        self.x1 = min(x, opposite.x)
        self.y1 = min(y, opposite.y)
        self.x2 = max(x, opposite.x)
        self.y2 = max(y, opposite.y)

    def delete_point(self, point_id: int | None) -> None:
        self.x1 = self.x2 = self.y1 = self.y2 = 0

    def copy(self) -> "BBox":
        copied = BBox(self.x1, self.y1, self.x2, self.y2, self.label)
        copied.show_label = self.show_label
        copied.show_size = self.show_size
        return copied

    def serialize(self) -> dict:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2, "label": self.label}

    def _color(self, labels: dict | None) -> tuple[int, int, int]:
        if labels and self.label in labels:
            return labels[self.label]
        return 0, 255, 255
