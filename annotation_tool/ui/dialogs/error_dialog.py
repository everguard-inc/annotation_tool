from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QPlainTextEdit, QPushButton, QVBoxLayout


class ErrorDialog(QDialog):
    def __init__(self, message: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Error")
        self.resize(720, 420)

        self.text = QPlainTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setPlainText(str(message))
        self.text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.close_button)

    @classmethod
    def show_error(cls, message: str, parent=None) -> None:
        dialog = cls(message, parent)
        dialog.exec()
