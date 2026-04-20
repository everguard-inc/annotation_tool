from PySide6.QtWidgets import QWidget

from annotation_tool.core.models import FilteringStatusData


class FilteringStatusBar(QWidget):
    def __init__(self, parent=None) -> None:
        ...

    def update_status(self, status: FilteringStatusData) -> None:
        ...
