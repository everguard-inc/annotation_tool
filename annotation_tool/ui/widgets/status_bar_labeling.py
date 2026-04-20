from PySide6.QtWidgets import QWidget

from annotation_tool.core.models import LabelingStatusData


class LabelingStatusBar(QWidget):
    def __init__(self, parent=None) -> None:
        ...

    def update_status(self, status: LabelingStatusData) -> None:
        ...
