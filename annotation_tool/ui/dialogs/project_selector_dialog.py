from PySide6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QVBoxLayout

from annotation_tool.core.models import ProjectData


class ProjectSelectorDialog(QDialog):
    def __init__(self, projects: list[ProjectData], title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(420, 520)

        self.projects = projects
        self.list_widget = QListWidget(self)

        for project in projects:
            item = QListWidgetItem(
                f"{project.id} | {project.stage.name} | {project.mode.name} | {project.uid or 'no uid'}"
            )
            item.setData(256, project)
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(lambda _: self.accept())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addWidget(buttons)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def selected_project(self) -> ProjectData | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(256)
