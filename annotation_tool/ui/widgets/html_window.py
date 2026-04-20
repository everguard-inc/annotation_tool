from pathlib import Path

from PySide6.QtWidgets import QWidget


class HtmlWindow(QWidget):
    def __init__(self, title: str, html_path: Path, parent=None) -> None:
        ...

    def show_file(self, html_path: Path) -> None:
        ...
