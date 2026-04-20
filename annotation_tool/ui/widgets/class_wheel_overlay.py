from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QWidget

from annotation_tool.core.models import LabelData


class ClassWheelOverlay(QWidget):
    def __init__(self, parent=None) -> None:
        ...

    def open_at(self, center: QPoint, labels: list[LabelData]) -> None:
        ...

    def selected_label(self, edge: QPoint) -> LabelData | None:
        ...

    def close(self) -> None:
        ...
