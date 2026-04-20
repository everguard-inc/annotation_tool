from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from annotation_tool.core.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(560, 360)

        self.token = QLineEdit(settings.token, self)
        self.api_url = QLineEdit(settings.api_url, self)
        self.file_url = QLineEdit(settings.file_url, self)
        self.data_dir = QLineEdit(str(settings.data_dir), self)

        self.bbox_line_width = self._number(settings.bbox_line_width, 1, 10, 1)
        self.cursor_proximity_threshold = self._number(settings.cursor_proximity_threshold, 1, 10, 1)
        self.objects_opacity = self._number(settings.objects_opacity, 0, 1, 0.1)
        self.color_fill_opacity = self._number(settings.color_fill_opacity, 0, 1, 0.1)
        self.bbox_handler_size = self._number(settings.bbox_handler_size, 1, 10, 1)
        self.keypoint_handler_size = self._number(settings.keypoint_handler_size, 1, 10, 1)

        form = QFormLayout()
        form.addRow("Token", self.token)
        form.addRow("API URL", self.api_url)
        form.addRow("File URL", self.file_url)
        form.addRow("Data dir", self.data_dir)
        form.addRow("BBox line width", self.bbox_line_width)
        form.addRow("Cursor proximity threshold", self.cursor_proximity_threshold)
        form.addRow("Objects opacity", self.objects_opacity)
        form.addRow("Color fill opacity", self.color_fill_opacity)
        form.addRow("BBox handler size", self.bbox_handler_size)
        form.addRow("Keypoint handler size", self.keypoint_handler_size)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def settings(self) -> AppSettings:
        return AppSettings(
            token=self.token.text().strip(),
            api_url=self.api_url.text().strip().rstrip("/"),
            file_url=self.file_url.text().strip().rstrip("/"),
            data_dir=Path(self.data_dir.text().strip()).expanduser(),
            bbox_line_width=self.bbox_line_width.value(),
            cursor_proximity_threshold=self.cursor_proximity_threshold.value(),
            objects_opacity=self.objects_opacity.value(),
            color_fill_opacity=self.color_fill_opacity.value(),
            bbox_handler_size=self.bbox_handler_size.value(),
            keypoint_handler_size=self.keypoint_handler_size.value(),
        )

    def _number(self, value: float, minimum: float, maximum: float, step: float) -> QDoubleSpinBox:
        field = QDoubleSpinBox(self)
        field.setRange(minimum, maximum)
        field.setSingleStep(step)
        field.setValue(value)
        return field
