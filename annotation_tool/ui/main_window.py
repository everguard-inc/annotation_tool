import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox

from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.settings import AppSettings, SettingsStore
from annotation_tool.infrastructure.api_client import ApiClient
from annotation_tool.ui.actions import AppActions
from annotation_tool.ui.dialogs.error_dialog import ErrorDialog
from annotation_tool.ui.dialogs.settings_dialog import SettingsDialog
from annotation_tool.ui.widgets.html_window import HtmlWindow


class MainWindow(QMainWindow):
    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()

        self.settings_store = settings_store
        self.settings: AppSettings | None = None
        self.api_client: ApiClient | None = None
        self.project_id: int | None = None
        self.html_windows: list[HtmlWindow] = []

        self.setWindowTitle("Annotation tool")
        self.resize(1200, 800)

        self.placeholder = QLabel("No project opened", self)
        self.placeholder.setMinimumSize(600, 400)
        self.placeholder.setStyleSheet("font-size: 18px;")
        self.setCentralWidget(self.placeholder)

        self.actions = AppActions(self)
        self.statusBar().showMessage("Ready")

        self._load_or_request_settings()

    def _load_or_request_settings(self) -> None:
        try:
            if self.settings_store.has_empty_required_values():
                self.open_settings()

            self.settings = self.settings_store.load()
            self.api_client = ApiClient(self.settings.api_url, self.settings.token)
        except UserVisibleError as error:
            ErrorDialog.show_error(str(error), self)
            self.open_settings()

    def set_current_project_title(self, project_id: int | None) -> None:
        self.project_id = project_id

        if project_id is None:
            self.setWindowTitle("Annotation tool")
            self.actions.set_project_opened(False)
            return

        self.setWindowTitle(f"Project {project_id}")
        self.actions.set_project_opened(True)

    def open_project(self) -> None:
        self._not_implemented_until_stage_2("Open project will be implemented in Stage 2.")

    def download_project(self) -> None:
        self._not_implemented_until_stage_2("Download project will be implemented in Stage 2.")

    def remove_project(self) -> None:
        self._not_implemented_until_stage_2("Remove project will be implemented in Stage 2.")

    def go_to_id(self) -> None:
        self._not_implemented_until_stage_2("Go to ID will be implemented in Stage 2.")

    def complete_project(self) -> None:
        if self.api_client is None:
            ErrorDialog.show_error("Backend is not configured.", self)
            return

        if not self.api_client.is_available():
            ErrorDialog.show_error(
                "Unable to reach a web service. Project is not completed.",
                self,
            )
            return

        self._not_implemented_until_stage_2("Project completion flow will be implemented in Stage 2.")

    def open_settings(self) -> None:
        try:
            current_settings = self._safe_settings_for_dialog()
            dialog = SettingsDialog(current_settings, self)

            if dialog.exec() != SettingsDialog.DialogCode.Accepted:
                return

            self.settings_store.save(dialog.settings())
            self.settings = self.settings_store.load()
            self.api_client = ApiClient(self.settings.api_url, self.settings.token)
            self.statusBar().showMessage("Settings saved", 3000)
        except UserVisibleError as error:
            ErrorDialog.show_error(str(error), self)

    def update_tool(self) -> None:
        agree = QMessageBox.question(
            self,
            "Tool update",
            "Are you sure you want to update annotation tool?",
        )

        if agree != QMessageBox.StandardButton.Yes:
            return

        root_path = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            ["git", "-C", str(root_path), "pull"],
            capture_output=True,
            text=True,
        )

        message = f"{result.stdout}\n{result.stderr}".strip()
        if "Updating" in message or "Fast-forward" in message:
            message += "\n\nSuccess\n\nRe-open the tool for the changes to take effect."

        QMessageBox.information(self, "Update result", message or "No output from git pull.")

    def show_help(self) -> None:
        self._show_html_window("How to use this tool?", "how.html")

    def show_hotkeys(self) -> None:
        self._show_html_window("Hotkeys", "hotkeys.html")

    def closeEvent(self, event) -> None:
        event.accept()

    def _safe_settings_for_dialog(self) -> AppSettings:
        if self.settings is not None:
            return self.settings

        try:
            return self.settings_store.load()
        except UserVisibleError:
            return AppSettings(
                token="",
                api_url="",
                file_url="",
                data_dir=Path.home() / "annotation",
                bbox_line_width=3.0,
                cursor_proximity_threshold=3.0,
                objects_opacity=0.9,
                color_fill_opacity=0.1,
                bbox_handler_size=3.0,
                keypoint_handler_size=5.0,
            )

    def _show_html_window(self, title: str, file_name: str) -> None:
        html_path = Path(__file__).resolve().parents[2] / "templates" / file_name
        window = HtmlWindow(title, html_path, self)
        window.show()
        self.html_windows.append(window)

    def _not_implemented_until_stage_2(self, message: str) -> None:
        QMessageBox.information(self, "Not implemented yet", message)


def run_app() -> None:
    app = QApplication(sys.argv)

    settings_path = Path(__file__).resolve().parents[2] / "settings.json"
    window = MainWindow(SettingsStore(settings_path))
    window.showMaximized()

    sys.exit(app.exec())
