from abc import ABC, abstractmethod
from enum import Enum, auto

import numpy as np

from annotation_tool.annotation.figures import Figure


class ControllerMode(Enum):
    IDLE = auto()
    CREATE = auto()
    MOVING = auto()


class FigureController(ABC):
    def set_figures(self, figures: list[Figure]) -> None:
        ...

    def figures(self) -> list[Figure]:
        ...

    def set_active_label(self, label_name: str, label_type: str) -> None:
        ...

    def handle_mouse_press(self, x: int, y: int) -> None:
        ...

    def handle_mouse_move(self, x: int, y: int) -> None:
        ...

    def handle_mouse_release(self, x: int, y: int) -> None:
        ...

    def handle_mouse_hover(self, x: int, y: int) -> None:
        ...

    def delete_selected(self) -> None:
        ...

    def delete_all(self) -> None:
        ...

    def copy(self) -> None:
        ...

    def paste(self) -> None:
        ...

    def undo(self) -> None:
        ...

    def redo(self) -> None:
        ...

    def set_shift_mode(self, enabled: bool) -> None:
        ...

    @abstractmethod
    def draw_overlay(self, frame: np.ndarray, scale_factor: float) -> np.ndarray:
        ...
