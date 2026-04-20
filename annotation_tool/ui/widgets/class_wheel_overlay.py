import math

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QWidget

from annotation_tool.core.models import LabelData


class ClassWheelOverlay(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.center = QPoint()
        self.labels: list[LabelData] = []

    def open_at(self, center: QPoint, labels: list[LabelData]) -> None:
        self.center = center
        self.labels = labels
        self.show()

    def selected_label(self, edge: QPoint) -> LabelData | None:
        if not self.labels:
            return None

        dx = edge.x() - self.center.x()
        dy = edge.y() - self.center.y()
        angle = math.atan2(dy, dx)

        if angle < 0:
            angle += 2 * math.pi

        index = int(angle / (2 * math.pi) * len(self.labels))
        index = max(0, min(index, len(self.labels) - 1))
        return self.labels[index]

    def close(self) -> None:
        self.hide()
