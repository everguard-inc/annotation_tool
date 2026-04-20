import numpy as np


def draw_text_label(frame: np.ndarray, text: str, x: int, y: int, color: tuple[int, int, int]) -> np.ndarray:
    ...


def draw_class_wheel(
    frame: np.ndarray,
    labels: list[str],
    colors: list[tuple[int, int, int]],
    center: tuple[int, int],
    edge: tuple[int, int],
) -> np.ndarray:
    ...


def selected_class_index(labels_count: int, center: tuple[int, int], edge: tuple[int, int]) -> int:
    ...
