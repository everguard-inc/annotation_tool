from PySide6.QtWidgets import QLabel, QVBoxLayout

from annotation_tool.core.models import ProjectData
from annotation_tool.ui.screens.base_screen import BaseProjectScreen


class ProjectPlaceholderScreen(BaseProjectScreen):
    def __init__(self, project: ProjectData, parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self._items_count = 1
        self._duration_hours = 0.0
        self.current_item_id = 0

        label = QLabel(
            f"Project {project.id}\n{project.stage.name} / {project.mode.name}\n\n"
            "Annotation screen will be implemented in the next stages.",
            self,
        )
        label.setStyleSheet("font-size: 18px;")

        layout = QVBoxLayout(self)
        layout.addWidget(label)

    @property
    def items_count(self) -> int:
        return self._items_count

    @property
    def duration_hours(self) -> float:
        return self._duration_hours

    def save(self) -> None:
        pass

    def close_screen(self) -> None:
        self.save()

    def go_to_id(self, item_id: int) -> None:
        self.current_item_id = max(0, min(item_id, self.items_count - 1))
