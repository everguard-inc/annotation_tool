from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from annotation_tool.core.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings: AppSettings,
        parent=None,
        required_mode: bool = False,
        missing_fields: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.required_mode = required_mode
        self.setWindowTitle("Settings")
        self.resize(520, 420)

        self.token_input = QLineEdit(settings.token, self)
        self.api_url_input = QLineEdit(settings.api_url, self)
        self.file_url_input = QLineEdit(settings.file_url, self)
        self.data_dir_input = QLineEdit(str(settings.data_dir), self)

        self.bbox_line_width_input = self._number_input(settings.bbox_line_width, 1, 10, 1)
        self.cursor_proximity_threshold_input = self._number_input(settings.cursor_proximity_threshold, 1, 10, 1)
        self.objects_opacity_input = self._number_input(settings.objects_opacity, 0, 1, 0.1)
        self.color_fill_opacity_input = self._number_input(settings.color_fill_opacity, 0, 1, 0.1)
        self.bbox_handler_size_input = self._number_input(settings.bbox_handler_size, 1, 10, 1)
        self.keypoint_handler_size_input = self._number_input(settings.keypoint_handler_size, 1, 10, 1)

        form = QFormLayout()
        form.addRow("Token", self.token_input)
        form.addRow("API URL", self.api_url_input)
        form.addRow("File URL", self.file_url_input)
        form.addRow("Data directory", self.data_dir_input)
        form.addRow("BBox line width", self.bbox_line_width_input)
        form.addRow("Cursor proximity threshold", self.cursor_proximity_threshold_input)
        form.addRow("Objects opacity", self.objects_opacity_input)
        form.addRow("Color fill opacity", self.color_fill_opacity_input)
        form.addRow("BBox handler size", self.bbox_handler_size_input)
        form.addRow("Keypoint handler size", self.keypoint_handler_size_input)

        buttons = QDialogButtonBox(self)
        self.save_button = buttons.addButton("Save", QDialogButtonBox.ButtonRole.AcceptRole)

        if required_mode:
            self.cancel_button = buttons.addButton("Cancel and exit", QDialogButtonBox.ButtonRole.RejectRole)
        else:
            self.cancel_button = buttons.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)

        if required_mode:
            missing = ", ".join(missing_fields or ["token", "api_url", "file_url", "data_dir"])
            message = (
                f"The following required settings are missing: {missing}.\n"
                "Please fill them in to continue using the application."
            )
            label = QLabel(message, self)
            label.setWordWrap(True)
            layout.addWidget(label)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def accept(self) -> None:
        missing = self._missing_required_values()
        if missing:
            QMessageBox.warning(
                self,
                "Missing settings",
                f"Please fill in required settings: {', '.join(missing)}.",
            )
            return

        super().accept()

    def reject(self) -> None:
        super().reject()

    def closeEvent(self, event) -> None:
        if self.required_mode and self._missing_required_values():
            self.reject()
        event.accept()

    def settings(self) -> AppSettings:
        return AppSettings(
            token=self.token_input.text().strip(),
            api_url=self.api_url_input.text().strip().rstrip("/"),
            file_url=self.file_url_input.text().strip().rstrip("/"),
            data_dir=Path(self.data_dir_input.text().strip()).expanduser(),
            bbox_line_width=self.bbox_line_width_input.value(),
            cursor_proximity_threshold=self.cursor_proximity_threshold_input.value(),
            objects_opacity=self.objects_opacity_input.value(),
            color_fill_opacity=self.color_fill_opacity_input.value(),
            bbox_handler_size=self.bbox_handler_size_input.value(),
            keypoint_handler_size=self.keypoint_handler_size_input.value(),
        )

    def _missing_required_values(self) -> list[str]:
        values = {
            "token": self.token_input.text(),
            "api_url": self.api_url_input.text(),
            "file_url": self.file_url_input.text(),
            "data_dir": self.data_dir_input.text(),
        }
        return [name for name, value in values.items() if not value.strip()]

    def _number_input(self, value: float, minimum: float, maximum: float, step: float) -> QDoubleSpinBox:
        field = QDoubleSpinBox(self)
        field.setRange(minimum, maximum)
        field.setSingleStep(step)
        field.setValue(value)
        return field