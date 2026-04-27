from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class Point:
    x: int
    y: int
    label: str | None = None

    def close_to(self, x: int, y: int, distance: float) -> bool:
        return abs(self.x - x) <= distance and abs(self.y - y) <= distance


@dataclass(frozen=True)
class AnnotationStyle:
    bbox_line_width: float = 3.0
    cursor_proximity_threshold: float = 3.0
    objects_opacity: float = 0.9
    color_fill_opacity: float = 0.1
    bbox_handler_size: float = 3.0
    keypoint_handler_size: float = 5.0

    @classmethod
    def from_settings(cls, settings) -> "AnnotationStyle":
        return cls(
            bbox_line_width=settings.bbox_line_width,
            cursor_proximity_threshold=settings.cursor_proximity_threshold,
            objects_opacity=settings.objects_opacity,
            color_fill_opacity=settings.color_fill_opacity,
            bbox_handler_size=settings.bbox_handler_size,
            keypoint_handler_size=settings.keypoint_handler_size,
        )


class Figure(ABC):
    selected: bool = False
    active_point_id: int | None = None

    @property
    @abstractmethod
    def figure_type(self) -> str:
        ...

    @property
    @abstractmethod
    def surface(self) -> int:
        ...

    @abstractmethod
    def draw(
        self,
        frame: np.ndarray,
        scale_factor: float,
        labels: dict | None = None,
        style: AnnotationStyle | None = None,
    ) -> np.ndarray:
        ...

    @abstractmethod
    def contains_point(self, point: Point) -> bool:
        ...

    @abstractmethod
    def find_nearest_point_index(self, x: int, y: int, distance: float = 5) -> int | None:
        ...

    @abstractmethod
    def move_active_point(self, x: int, y: int) -> None:
        ...

    @abstractmethod
    def delete_point(self, point_id: int | None) -> None:
        ...

    @abstractmethod
    def copy(self) -> "Figure":
        ...

    @abstractmethod
    def serialize(self) -> dict:
        ...
