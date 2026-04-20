import sys
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextEdit, QVBoxLayout, QWidget


class ErrorDialog(QDialog):
    def __init__(self, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Error")
        self.resize(900, 600)

        self.text = QTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text.setText(message)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Copy this error and send it to technical support if needed.", self))
        layout.addWidget(self.text)
        layout.addWidget(buttons)

    @staticmethod
    def show_error(message: str, parent: QWidget | None = None) -> None:
        dialog = ErrorDialog(message, parent)
        dialog.exec()


def format_exception(exc_type, exc_value, exc_traceback) -> str:
    return "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))


def show_unhandled_exception(exc_type, exc_value, exc_traceback, *, critical: bool) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    ErrorDialog.show_error(format_exception(exc_type, exc_value, exc_traceback))

    if critical:
        sys.exit(1)
