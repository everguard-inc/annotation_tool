from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow


class AppActions:
    def __init__(self, window: QMainWindow) -> None:
        ...

    def create_actions(self) -> None:
        ...

    def bind_menu(self) -> None:
        ...

    def set_project_opened(self, opened: bool) -> None:
        ...
