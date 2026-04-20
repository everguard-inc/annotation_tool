import cv2
import numpy as np

from annotation_tool.annotation.figures import Figure, Point


class KeypointGroup(Figure):
    def __init__(self, label: str, keypoints: list[Point], attributes: dict | None = None) -> None:
        self.label = label
        self.keypoints = keypoints
        self.attributes = attributes or {}
        self.selected = False
        self.active_point_id: int | None = None
        self.show_names = False

    @classmethod
    def from_box(
        cls,
        start: Point,
        end: Point,
        label: str,
        keypoint_template: dict,
    ) -> "KeypointGroup | None":
        if abs(start.x - end.x) < 3 or abs(start.y - end.y) < 3:
            return None

        reflect_x = end.x < start.x
        reflect_y = end.y < start.y

        width = abs(end.x - start.x)
        height = abs(end.y - start.y)

        keypoints = []
        for name, data in keypoint_template.get("keypoint_info", {}).items():
            rel_x = float(data.get("x", 0))
            rel_y = float(data.get("y", 0))

            x = start.x - rel_x * width if reflect_x else start.x + rel_x * width
            y = start.y - rel_y * height if reflect_y else start.y + rel_y * height

            keypoints.append(Point(x=int(x), y=int(y), label=name))

        return cls(label=label, keypoints=keypoints, attributes=keypoint_template)

    @property
    def figure_type(self) -> str:
        return "KGROUP"

    @property
    def surface(self) -> int:
        return 1 if self.keypoints else 0

    def draw(self, frame: np.ndarray, scale_factor: float, labels: dict | None = None) -> np.ndarray:
        keypoints_by_name = {point.label: point for point in self.keypoints}
        connections = self.attributes.get("keypoint_connections", [])
        info = self.attributes.get("keypoint_info", {})

        for connection in connections:
            p1 = keypoints_by_name.get(connection.get("from"))
            p2 = keypoints_by_name.get(connection.get("to"))
            if p1 and p2:
                cv2.line(frame, (p1.x, p1.y), (p2.x, p2.y), self._color(connection.get("color")), 2)

        for index, point in enumerate(self.keypoints):
            color = self._color(info.get(point.label, {}).get("color"))
            radius = 6 if index == self.active_point_id else 4
            cv2.circle(frame, (point.x, point.y), radius, color, -1)

            if self.show_names and point.label:
                cv2.putText(
                    frame,
                    point.label,
                    (point.x + 5, point.y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )

        return frame

    def contains_point(self, point: Point) -> bool:
        return False

    def find_nearest_point_index(self, x: int, y: int, distance: float = 5) -> int | None:
        for index, point in enumerate(self.keypoints):
            if point.close_to(x, y, distance):
                return index
        return None

    def move_active_point(self, x: int, y: int) -> None:
        if self.active_point_id is None:
            return

        self.keypoints[self.active_point_id].x = x
        self.keypoints[self.active_point_id].y = y

    def delete_point(self, point_id: int | None) -> None:
        if point_id is None:
            self.keypoints = []
            return

        if 0 <= point_id < len(self.keypoints):
            self.keypoints.pop(point_id)

        if len(self.keypoints) <= 1:
            self.keypoints = []

    def copy(self) -> "KeypointGroup":
        copied = KeypointGroup(
            label=self.label,
            keypoints=[Point(point.x, point.y, point.label) for point in self.keypoints],
            attributes=self.attributes,
        )
        copied.show_names = self.show_names
        return copied

    def serialize(self) -> dict:
        return {
            "label": self.label,
            "points": [{"x": point.x, "y": point.y, "label": point.label} for point in self.keypoints],
        }

    def _color(self, name: str | None) -> tuple[int, int, int]:
        colors = {
            "red": (0, 0, 255),
            "lime": (0, 255, 0),
            "green": (0, 128, 0),
            "blue": (255, 0, 0),
            "yellow": (0, 255, 255),
            "cyan": (255, 255, 0),
            "magenta": (255, 0, 255),
            "gray": (192, 192, 192),
            "white": (255, 255, 255),
        }
        return colors.get(name or "", colors["white"])
