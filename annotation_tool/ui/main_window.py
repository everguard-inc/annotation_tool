from PySide6.QtWidgets import QMainWindow, QApplication


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        ...

    def open_project(self) -> None:
        ...

    def download_project(self) -> None:
        ...

    def remove_project(self) -> None:
        ...

    def complete_project(self) -> None:
        ...

    def open_settings(self) -> None:
        ...

    def update_tool(self) -> None:
        ...

    def show_help(self) -> None:
        ...

    def show_hotkeys(self) -> None:
        ...

    def closeEvent(self, event) -> None:
        ...


def run_app() -> None:
    ...
