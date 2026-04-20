from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class Point:
    x: int
    y: int
    label: str | None = None

    def close_to(self, x: int, y: int, distance: float) -> bool:
        ...


class Figure(ABC):
    selected: bool

    @property
    @abstractmethod
    def figure_type(self) -> str:
        ...

    @property
    @abstractmethod
    def surface(self) -> int:
        ...

    @abstractmethod
    def draw(self, frame: np.ndarray, scale_factor: float) -> np.ndarray:
        ...

    @abstractmethod
    def contains_point(self, point: Point) -> bool:
        ...

    @abstractmethod
    def find_nearest_point_index(self, x: int, y: int) -> int | None:
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
