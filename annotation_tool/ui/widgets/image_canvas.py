from PySide6.QtCore import QPoint, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QWidget


class ImageCanvas(QWidget):
    mouse_pressed = Signal(int, int)
    mouse_moved = Signal(int, int)
    mouse_released = Signal(int, int)
    mouse_hovered = Signal(int, int)
    key_pressed = Signal(str)
    key_released = Signal(str)

    def __init__(self, parent=None) -> None:
        ...

    def set_image(self, image: QImage) -> None:
        ...

    def set_overlay_enabled(self, enabled: bool) -> None:
        ...

    def fit_image(self) -> None:
        ...

    def image_coordinates(self, point: QPoint) -> tuple[int, int]:
        ...

    def paintEvent(self, event) -> None:
        ...

    def mousePressEvent(self, event) -> None:
        ...

    def mouseMoveEvent(self, event) -> None:
        ...

    def mouseReleaseEvent(self, event) -> None:
        ...

    def wheelEvent(self, event) -> None:
        ...

    def keyPressEvent(self, event) -> None:
        ...

    def keyReleaseEvent(self, event) -> None:
        ...
