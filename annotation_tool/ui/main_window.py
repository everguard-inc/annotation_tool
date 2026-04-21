import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox

from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.models import ProjectData
from annotation_tool.core.settings import AppSettings, SettingsStore
from annotation_tool.infrastructure.api_client import ApiClient
from annotation_tool.infrastructure.file_transfer import FileTransferClient
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.infrastructure.unzip import ArchiveUnzipper
from annotation_tool.services.completion_service import CompletionService
from annotation_tool.services.import_export_service import ImportExportService
from annotation_tool.services.project_service import ProjectService
from annotation_tool.ui.actions import AppActions
from annotation_tool.ui.dialogs.error_dialog import ErrorDialog
from annotation_tool.ui.dialogs.id_dialog import IdDialog
from annotation_tool.ui.dialogs.progress_dialog import ProgressDialog
from annotation_tool.ui.dialogs.project_selector_dialog import ProjectSelectorDialog
from annotation_tool.ui.dialogs.settings_dialog import SettingsDialog
from annotation_tool.ui.screens.base_screen import BaseProjectScreen
from annotation_tool.ui.screens.project_placeholder_screen import ProjectPlaceholderScreen
from annotation_tool.ui.widgets.html_window import HtmlWindow


class MainWindow(QMainWindow):
    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()

        self.settings_store = settings_store
        self.settings: AppSettings | None = None
        self.api_client: ApiClient | None = None
        self.project_service: ProjectService | None = None
        self.completion_service: CompletionService | None = None
        self.import_export_service: ImportExportService | None = None

        self.current_project: ProjectData | None = None
        self.current_screen: BaseProjectScreen | None = None
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
        if self.settings_store.has_empty_required_values():
            accepted = self.open_required_settings()
            if not accepted:
                QApplication.instance().quit()
                raise SystemExit(0)

        self.settings = self.settings_store.load()
        self._build_services()

    def _build_services(self) -> None:
        if self.settings is None:
            return

        self.api_client = ApiClient(self.settings.api_url, self.settings.token)
        file_transfer = FileTransferClient(self.settings.file_url, self.settings.token)
        repository = ProjectRepository(self.settings.data_dir)

        self.import_export_service = ImportExportService(
            data_dir=self.settings.data_dir,
            file_transfer=file_transfer,
            unzipper=ArchiveUnzipper(),
        )
        self.project_service = ProjectService(self.api_client, repository, self.import_export_service)
        self.completion_service = CompletionService(
            self.api_client,
            repository,
            file_transfer=file_transfer,
            import_export_service=self.import_export_service,
        )

    def set_current_project_title(self, project_id: int | None) -> None:
        if project_id is None:
            self.setWindowTitle("Annotation tool")
            self.actions.set_project_opened(False)
            return

        self.setWindowTitle(f"Project {project_id}")
        self.actions.set_project_opened(True)

    def open_project(self) -> None:
        if self.project_service is None:
            raise RuntimeError("Project service is not configured.")

        projects = self.project_service.get_available_projects()
        if not projects:
            QMessageBox.information(self, "Projects", "No projects available.")
            return

        project = self._select_project(projects, "Open project")
        if project is None:
            return

        progress = self._progress("Opening project")
        opened_project = self.project_service.open_project(project, progress=progress.update_progress)
        progress.mark_complete()

        self._set_project_screen(opened_project)

    def download_project(self) -> None:
        if self.project_service is None:
            raise RuntimeError("Project service is not configured.")

        projects = self.project_service.get_projects_from_backend()
        if not projects:
            QMessageBox.information(self, "Projects", "No projects available for download.")
            return

        project = self._select_project(projects, "Download project")
        if project is None:
            return

        progress = self._progress("Downloading project")
        self.project_service.download_project(project, progress=progress.update_progress)
        progress.mark_complete()

        opened_project = self.project_service.open_project(project)
        self._set_project_screen(opened_project)

    def remove_project(self) -> None:
        if self.project_service is None:
            ErrorDialog.show_error("Project service is not configured.", self)
            return

        projects = self.project_service.get_local_projects(include_broken=True)
        if not projects:
            QMessageBox.information(self, "Projects", "No local projects.")
            return

        project = self._select_project(projects, "Remove local project")
        if project is None:
            return

        agree = QMessageBox.question(self, "Remove project", f"Remove project {project.id} from this computer?")
        if agree != QMessageBox.StandardButton.Yes:
            return

        self.project_service.remove_project(project.id)

        if self.current_project is not None and self.current_project.id == project.id:
            self._close_current_project()

        QMessageBox.information(self, "Project removed", f"Project {project.id} removed.")

    def go_to_id(self) -> None:
        if self.current_screen is None:
            return

        dialog = IdDialog(self.current_screen.items_count, self)
        if dialog.exec() != IdDialog.DialogCode.Accepted:
            return

        selected_id = dialog.selected_id()
        if selected_id is None:
            return

        self.current_screen.go_to_id(selected_id - 1)
        self.statusBar().showMessage(f"Moved to item {selected_id}", 3000)

    def complete_project(self) -> None:
        if self.current_project is None or self.current_screen is None:
            return

        if self.completion_service is None:
            ErrorDialog.show_error("Completion service is not configured.", self)
            return

        agree = QMessageBox.question(
            self,
            "Project Completion",
            "Are you sure you want to complete the project?",
        )
        if agree != QMessageBox.StandardButton.Yes:
            return

        try:
            self.current_screen.save()

            completed_project = self.completion_service.complete_current_project(
                project=self.current_project,
                duration_hours=self.current_screen.duration_hours,
                export_results=self.current_screen.export_results,
                should_remove_after_completion=lambda _: self.current_screen.should_remove_after_completion(),
            )

            self.current_project = completed_project
            self._close_current_project()
            QMessageBox.information(self, "Success", "Project completed.")
        except UserVisibleError as error:
            ErrorDialog.show_error(str(error), self)

    def overwrite_annotations(self) -> None:
        if self.current_project is None or self.project_service is None:
            return

        agree = QMessageBox.question(
            self,
            "Overwrite",
            "Download annotations and overwrite local annotations?",
        )
        if agree != QMessageBox.StandardButton.Yes:
            return

        try:
            progress = self._progress("Overwriting annotations")
            self.project_service.overwrite_annotations(self.current_project, progress=progress.update_progress)
            progress.mark_complete()
            QMessageBox.information(self, "Success", "Annotations overwritten.")
        except UserVisibleError as error:
            ErrorDialog.show_error(str(error), self)

    def open_settings(self) -> None:
        current_settings = self._safe_settings_for_dialog()
        dialog = SettingsDialog(current_settings, self)

        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return

        self.settings_store.save(dialog.settings())
        self.settings = self.settings_store.load()
        self._build_services()
        self.statusBar().showMessage("Settings saved", 3000)

    def open_required_settings(self) -> bool:
        missing = self.settings_store.missing_required_values()
        dialog = SettingsDialog(
            self.settings_store.draft_settings(),
            self,
            required_mode=True,
            missing_fields=missing,
        )

        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return False

        self.settings_store.save(dialog.settings())
        return True

    def update_tool(self) -> None:
        agree = QMessageBox.question(
            self,
            "Tool update",
            "Are you sure you want to update annotation tool?",
        )

        if agree != QMessageBox.StandardButton.Yes:
            return

        root_path = Path(__file__).resolve().parents[2]
        python_path = root_path / "venv" / "bin" / "python"

        if not python_path.exists():
            python_path = Path(sys.executable)

        commands = [
            ["git", "-C", str(root_path), "pull"],
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            [str(python_path), "-m", "pip", "install", "-r", str(root_path / "requirements.txt")],
        ]

        output_parts = []

        for command in commands:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

            output_parts.append(f"$ {' '.join(command)}")
            output_parts.append(result.stdout.strip())
            output_parts.append(result.stderr.strip())

            if result.returncode != 0:
                message = "\n".join(part for part in output_parts if part)
                raise RuntimeError(f"Update failed.\n\n{message}")

        self._refresh_desktop_shortcut(root_path, python_path)

        message = "\n".join(part for part in output_parts if part)
        message += "\n\nSuccess\n\nRe-open the tool from the desktop shortcut for the changes to take effect."

        QMessageBox.information(self, "Update result", message)

    def _refresh_desktop_shortcut(self, root_path: Path, python_path: Path) -> None:
        desktop_path = Path.home() / "Desktop"
        if not desktop_path.exists():
            return

        desktop_file = desktop_path / "Labeling.desktop"
        icon_path = root_path / "icon.png"

        desktop_file.write_text(
            "\n".join(
                [
                    "[Desktop Entry]",
                    "Version=1.0",
                    "Type=Application",
                    "Name=EG Labeling",
                    f"Exec=bash -c 'cd \"{root_path}\" && \"{python_path}\" -m annotation_tool'",
                    f"Icon={icon_path}",
                    "Terminal=false",
                    "StartupNotify=true",
                    "Categories=Utility;",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        desktop_file.chmod(0o755)

    def show_help(self) -> None:
        self._show_html_window("How to use this tool?", "how.html")

    def show_hotkeys(self) -> None:
        self._show_html_window("Hotkeys", "hotkeys.html")

    def show_classes(self) -> None:
        if self.current_screen is not None and hasattr(self.current_screen, "show_classes"):
            self.current_screen.show_classes()

    def show_review_labels(self) -> None:
        if self.current_screen is not None and hasattr(self.current_screen, "show_review_labels"):
            self.current_screen.show_review_labels()

    def closeEvent(self, event) -> None:
        if self.current_screen is not None:
            self.current_screen.close_screen()
        event.accept()

    def _select_project(self, projects: list[ProjectData], title: str) -> ProjectData | None:
        dialog = ProjectSelectorDialog(projects, title, self)
        if dialog.exec() != ProjectSelectorDialog.DialogCode.Accepted:
            return None
        return dialog.selected_project()

    def _set_project_screen(self, project: ProjectData) -> None:
        if self.current_screen is not None:
            self.current_screen.close_screen()
            self.current_screen.deleteLater()

        self.current_project = project

        from annotation_tool.core.enums import AnnotationMode
        from annotation_tool.infrastructure.repositories.filtering_repository import FilteringRepository
        from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
        from annotation_tool.media.video_frame_provider import VideoFrameProvider
        from annotation_tool.services.filtering_session import FilteringSession
        from annotation_tool.services.labeling_session import LabelingSession
        from annotation_tool.ui.screens.filtering_screen import FilteringScreen
        from annotation_tool.ui.screens.labeling_screen import LabelingScreen

        if self.settings is not None and project.mode in {
            AnnotationMode.OBJECT_DETECTION,
            AnnotationMode.SEGMENTATION,
            AnnotationMode.KEYPOINTS,
        }:
            repository = LabelingRepository(self.settings.data_dir, project.id)
            session = LabelingSession(project, repository)
            self.current_screen = LabelingScreen(session, self)

        elif self.settings is not None and project.mode is AnnotationMode.FILTERING:
            from annotation_tool.core.paths import FilteringPaths

            paths = FilteringPaths(self.settings.data_dir, project.id)
            repository = FilteringRepository(self.settings.data_dir, project.id)
            frame_provider = VideoFrameProvider(paths.video_path)
            session = FilteringSession(frame_provider, repository)
            self.current_screen = FilteringScreen(session, paths.selected_frames_path, self)

        else:
            self.current_screen = ProjectPlaceholderScreen(project, self)

        self.setCentralWidget(self.current_screen)
        self.set_current_project_title(project.id)

    def _close_current_project(self) -> None:
        if self.current_screen is not None:
            self.current_screen.close_screen()
            self.current_screen.deleteLater()

        self.current_project = None
        self.current_screen = None
        self.placeholder = QLabel("No project opened", self)
        self.placeholder.setStyleSheet("font-size: 18px;")
        self.setCentralWidget(self.placeholder)
        self.set_current_project_title(None)

    def _safe_settings_for_dialog(self) -> AppSettings:
        if self.settings is not None:
            return self.settings

        return self.settings_store.draft_settings()

    def _show_html_window(self, title: str, file_name: str) -> None:
        html_path = Path(__file__).resolve().parents[2] / "templates" / file_name
        window = HtmlWindow(title, html_path, self)
        window.show()
        self.html_windows.append(window)

    def _progress(self, title: str) -> ProgressDialog:
        dialog = ProgressDialog(title, self)
        dialog.show()
        QApplication.processEvents()
        return dialog


def run_app() -> None:
    from annotation_tool.ui.exception_hook import ErrorAwareApplication, install_exception_hooks

    install_exception_hooks()

    app = ErrorAwareApplication(sys.argv)

    settings_path = Path(__file__).resolve().parents[2] / "settings.json"
    window = MainWindow(SettingsStore(settings_path))
    window.showMaximized()

    sys.exit(app.exec())
