from PySide6.QtWidgets import QDialog


class ErrorDialog(QDialog):
    def __init__(self, message: str, parent=None) -> None:
        ...

    @classmethod
    def show_error(cls, message: str, parent=None) -> None:
        ...
