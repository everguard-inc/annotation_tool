from PySide6.QtWidgets import QDialog

from annotation_tool.core.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        ...

    def settings(self) -> AppSettings:
        ...
