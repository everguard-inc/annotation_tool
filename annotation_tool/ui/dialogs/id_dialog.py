from PySide6.QtWidgets import QDialog, QDialogButtonBox, QSpinBox, QVBoxLayout


class IdDialog(QDialog):
    def __init__(self, max_id: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Go to ID")

        self.id_input = QSpinBox(self)
        self.id_input.setRange(1, max(max_id, 1))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.id_input)
        layout.addWidget(buttons)

    def selected_id(self) -> int | None:
        if self.result() != QDialog.DialogCode.Accepted:
            return None
        return self.id_input.value()
