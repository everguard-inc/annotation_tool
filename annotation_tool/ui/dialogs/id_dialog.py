from PySide6.QtWidgets import QDialog


class IdDialog(QDialog):
    def __init__(self, max_id: int, parent=None) -> None:
        ...

    def selected_id(self) -> int | None:
        ...
