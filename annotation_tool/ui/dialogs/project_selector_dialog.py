from PySide6.QtWidgets import QDialog

from annotation_tool.core.models import ProjectData


class ProjectSelectorDialog(QDialog):
    def __init__(self, projects: list[ProjectData], title: str, parent=None) -> None:
        ...

    def selected_project(self) -> ProjectData | None:
        ...
