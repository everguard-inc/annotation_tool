from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow


class AppActions:
    def __init__(self, window: QMainWindow) -> None:
        self.window = window
        self.project_opened = False
        self.create_actions()
        self.bind_menu()

    def create_actions(self) -> None:
        self.open_action = QAction("Open", self.window)
        self.download_action = QAction("Download", self.window)
        self.settings_action = QAction("Settings", self.window)
        self.update_action = QAction("Update tool", self.window)
        self.remove_action = QAction("Remove project by ID", self.window)
        self.go_to_id_action = QAction("Go to ID", self.window)
        self.complete_action = QAction("Complete the project", self.window)

        self.help_action = QAction("How to use this tool?", self.window)
        self.hotkeys_action = QAction("Hotkeys", self.window)

        self.open_action.triggered.connect(self.window.open_project)
        self.download_action.triggered.connect(self.window.download_project)
        self.settings_action.triggered.connect(self.window.open_settings)
        self.update_action.triggered.connect(self.window.update_tool)
        self.remove_action.triggered.connect(self.window.remove_project)
        self.go_to_id_action.triggered.connect(self.window.go_to_id)
        self.complete_action.triggered.connect(self.window.complete_project)
        self.help_action.triggered.connect(self.window.show_help)
        self.hotkeys_action.triggered.connect(self.window.show_hotkeys)

    def bind_menu(self) -> None:
        menu = self.window.menuBar()

        self.project_menu = menu.addMenu("Project")
        self.project_menu.addAction(self.open_action)
        self.project_menu.addAction(self.download_action)
        self.project_menu.addAction(self.settings_action)
        self.project_menu.addAction(self.update_action)
        self.project_menu.addAction(self.remove_action)
        self.project_menu.addSeparator()
        self.project_menu.addAction(self.go_to_id_action)
        self.project_menu.addAction(self.complete_action)

        self.help_menu = menu.addMenu("Help")
        self.help_menu.addAction(self.help_action)
        self.help_menu.addAction(self.hotkeys_action)

        self.set_project_opened(False)

    def set_project_opened(self, opened: bool) -> None:
        self.project_opened = opened
        self.go_to_id_action.setEnabled(opened)
        self.complete_action.setEnabled(opened)
