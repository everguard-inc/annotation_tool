from pathlib import Path

from PySide6.QtCore import Qt

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.models import ProjectData
from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui import main_window as main_window_module
from annotation_tool.ui.main_window import MainWindow


def test_main_window_updates_title_and_project_actions(
    qapp, valid_settings_file: Path
) -> None:
    """Covers FR-182."""
    window = MainWindow(SettingsStore(valid_settings_file))

    window.set_current_project_title(42)

    assert window.windowTitle() == "Project 42"
    assert window.actions.go_to_id_action.isEnabled()
    assert window.actions.complete_action.isEnabled()

    window.set_current_project_title(None)

    assert window.windowTitle() == "Annotation tool"
    assert not window.actions.go_to_id_action.isEnabled()
    assert not window.actions.complete_action.isEnabled()


def test_main_window_boots_with_icon_menubar_maximized_and_workspace(
    qapp, valid_settings_file: Path
) -> None:
    """Covers FR-001. App must launch with an icon, a menu bar (Project +
    Help), maximized window state, and a central workspace widget."""
    window = MainWindow(SettingsStore(valid_settings_file))

    assert not window.windowIcon().isNull()

    assert window.windowState() & Qt.WindowState.WindowMaximized

    menu_bar = window.menuBar()
    menu_titles = [action.text() for action in menu_bar.actions()]
    assert menu_titles == ["Project", "Help"]

    assert window.centralWidget() is not None


def test_main_window_empty_state_text_is_centered(
    qapp, valid_settings_file: Path
) -> None:
    window = MainWindow(SettingsStore(valid_settings_file))

    assert window.placeholder.alignment() == Qt.AlignmentFlag.AlignCenter


def test_main_window_starts_stale_project_cleanup_on_startup(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    calls = []

    def fake_start_cleanup(self):
        calls.append(self.project_service)

    monkeypatch.setattr(
        MainWindow, "_start_completed_project_cleanup", fake_start_cleanup, raising=False
    )

    MainWindow(SettingsStore(valid_settings_file))

    assert len(calls) == 1
    assert calls[0] is not None


def test_download_project_passes_progress_cancellation_callback(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    project = ProjectData(
        id=7,
        uid="uid-7",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    captured = {}

    class FakeProjectService:
        def get_projects_from_backend(self):
            return [project]

        def download_project(self, selected_project, progress=None, should_cancel=None):
            captured["project"] = selected_project
            captured["progress"] = progress
            captured["should_cancel"] = should_cancel

    class FakeProgress:
        def __init__(self):
            self.completed = False

        def update_progress(self, *args):
            pass

        def should_cancel(self):
            return True

        def mark_complete(self):
            self.completed = True

    fake_progress = FakeProgress()
    monkeypatch.setattr(MainWindow, "_start_completed_project_cleanup", lambda self: None, raising=False)
    window = MainWindow(SettingsStore(valid_settings_file))
    window.project_service = FakeProjectService()
    monkeypatch.setattr(window, "_select_project", lambda projects, title: project)
    monkeypatch.setattr(window, "_progress", lambda title: fake_progress)

    window.download_project()

    assert captured == {
        "project": project,
        "progress": fake_progress.update_progress,
        "should_cancel": fake_progress.should_cancel,
    }
    assert fake_progress.completed is True


def test_download_project_closes_progress_on_user_visible_error(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    project = ProjectData(
        id=7,
        uid="uid-7",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    errors = []

    class FakeProjectService:
        def get_projects_from_backend(self):
            return [project]

        def download_project(self, selected_project, progress=None, should_cancel=None):
            raise UserVisibleError("download failed")

    class FakeProgress:
        completed = False
        closed = False

        def update_progress(self, *args):
            pass

        def should_cancel(self):
            return False

        def mark_complete(self):
            self.completed = True

        def close(self):
            self.closed = True

    fake_progress = FakeProgress()
    monkeypatch.setattr(
        MainWindow, "_start_completed_project_cleanup", lambda self: None, raising=False
    )
    monkeypatch.setattr(
        main_window_module.ErrorDialog,
        "show_error",
        staticmethod(lambda message, parent=None: errors.append(message)),
    )
    window = MainWindow(SettingsStore(valid_settings_file))
    window.project_service = FakeProjectService()
    monkeypatch.setattr(window, "_select_project", lambda projects, title: project)
    monkeypatch.setattr(window, "_progress", lambda title: fake_progress)

    window.download_project()

    assert errors == ["download failed"]
    assert fake_progress.closed is True
    assert fake_progress.completed is False


def test_open_project_closes_progress_on_user_visible_error_without_mounting_screen(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    project = ProjectData(
        id=7,
        uid="uid-7",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    errors = []
    mounted = []

    class FakeProjectService:
        def get_available_projects(self):
            return [project]

        def open_project(self, selected_project, progress=None, should_cancel=None):
            raise UserVisibleError("open failed")

    class FakeProgress:
        completed = False
        closed = False

        def update_progress(self, *args):
            pass

        def should_cancel(self):
            return False

        def mark_complete(self):
            self.completed = True

        def close(self):
            self.closed = True

    fake_progress = FakeProgress()
    monkeypatch.setattr(
        MainWindow, "_start_completed_project_cleanup", lambda self: None, raising=False
    )
    monkeypatch.setattr(
        main_window_module.ErrorDialog,
        "show_error",
        staticmethod(lambda message, parent=None: errors.append(message)),
    )
    window = MainWindow(SettingsStore(valid_settings_file))
    window.project_service = FakeProjectService()
    monkeypatch.setattr(window, "_select_project", lambda projects, title: project)
    monkeypatch.setattr(window, "_progress", lambda title: fake_progress)
    monkeypatch.setattr(window, "_set_project_screen", lambda project: mounted.append(project))

    window.open_project()

    assert errors == ["open failed"]
    assert fake_progress.closed is True
    assert fake_progress.completed is False
    assert mounted == []
