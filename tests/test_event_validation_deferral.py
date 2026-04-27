import inspect
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PySide6.QtWidgets import QComboBox, QPushButton, QSlider, QWidget

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.settings import SettingsStore
from annotation_tool.core.utils import read_json
from annotation_tool.ui import main_window
from annotation_tool.ui.main_window import MainWindow
from annotation_tool.ui.screens.event_validation_screen import EventValidationScreen


def _ev_project() -> ProjectData:
    return ProjectData(
        id=42,
        uid="ev-uid",
        stage=AnnotationStage.EVENT_VALIDATION,
        mode=AnnotationMode.EVENT_VALIDATION,
    )


def test_main_window_has_no_event_validation_deferral_guards() -> None:
    source = inspect.getsource(main_window)

    assert "EVENT_VALIDATION_DEFERRAL_MESSAGE" not in source
    assert "Event validation not available" not in source
    assert "Please complete this project in the Tk build" not in source


def test_main_window_routes_event_validation_to_screen(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    window = MainWindow(SettingsStore(valid_settings_file))
    window.settings = SimpleNamespace(data_dir=Path("/tmp/ev-test-data"))
    project = _ev_project()
    created = {}

    class FakePaths:
        runtime_state_path = Path("/tmp/runtime_state.json")
        db_path = Path("/tmp/db.sqlite")
        statistics_path = Path("/tmp/statistics.txt")
        results_path = Path("/tmp/event_validation_results.json")

        def __init__(self, data_dir, project_id):
            created["paths"] = (data_dir, project_id)

    class FakeRepository:
        def __init__(self, data_dir, project_id):
            created["repository"] = (data_dir, project_id)

    class FakeSession:
        def __init__(
            self, project_data, repository, session_state_store, statistics_service=None
        ):
            created["session_project"] = project_data

    class FakeScreen(QWidget):
        def __init__(self, session, results_path, parent=None):
            super().__init__(parent)
            created["screen"] = (session, results_path, parent)

        def close_screen(self):
            pass

    monkeypatch.setattr(main_window, "EventValidationPaths", FakePaths)
    monkeypatch.setattr(main_window, "EventValidationRepository", FakeRepository)
    monkeypatch.setattr(main_window, "EventValidationSession", FakeSession)
    monkeypatch.setattr(main_window, "EventValidationScreen", FakeScreen)
    monkeypatch.setattr(
        main_window, "SessionStateStore", lambda *args, **kwargs: object()
    )
    monkeypatch.setattr(
        main_window, "StatisticsService", lambda *args, **kwargs: object()
    )

    window._set_project_screen(project)

    assert created["session_project"] == project
    assert window.current_project == project
    assert window.windowTitle() == "Project 42"


def test_open_project_accepts_event_validation_project(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    window = MainWindow(SettingsStore(valid_settings_file))
    project = _ev_project()
    calls = {}

    class FakeProgress:
        def update_progress(self, *args, **kwargs):
            pass

        def should_cancel(self):
            return False

        def mark_complete(self):
            calls["progress_complete"] = True

    class FakeProjectService:
        def get_available_projects(self):
            return [project]

        def open_project(self, selected_project, progress=None, should_cancel=None):
            calls["opened"] = selected_project
            if progress is not None:
                progress(1, 1)
            return selected_project

    window.project_service = FakeProjectService()
    monkeypatch.setattr(window, "_select_project", lambda projects, title: project)
    monkeypatch.setattr(window, "_progress", lambda title: FakeProgress())
    monkeypatch.setattr(
        window,
        "_set_project_screen",
        lambda opened_project: calls.setdefault("screen", opened_project),
    )

    window.open_project()

    assert calls["opened"] == project
    assert calls["screen"] == project
    assert calls["progress_complete"] is True


def test_download_project_downloads_event_validation_without_opening(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    window = MainWindow(SettingsStore(valid_settings_file))
    project = _ev_project()
    calls = {}

    class FakeProgress:
        def update_progress(self, *args, **kwargs):
            pass

        def should_cancel(self):
            return False

        def mark_complete(self):
            calls["progress_complete"] = True

    class FakeProjectService:
        def get_projects_from_backend(self):
            return [project]

        def download_project(self, selected_project, progress=None, should_cancel=None):
            calls["downloaded"] = selected_project
            if progress is not None:
                progress(1, 1)

    window.project_service = FakeProjectService()
    monkeypatch.setattr(window, "_select_project", lambda projects, title: project)
    monkeypatch.setattr(window, "_progress", lambda title: FakeProgress())
    monkeypatch.setattr(
        window,
        "_set_project_screen",
        lambda opened_project: calls.setdefault("screen", opened_project),
    )

    window.download_project()

    assert calls["downloaded"] == project
    assert "screen" not in calls
    assert calls["progress_complete"] is True


def test_event_validation_screen_exports_results(tmp_path: Path) -> None:
    class FakeRepository:
        def events(self):
            return [
                {
                    "uid": "ev-a",
                    "answers": ["TP"],
                    "comment": "checked",
                }
            ]

    class FakeSession:
        duration_hours = 0.0
        fields = {"Status": {"TP": "green", "FP": "red"}}
        repository = FakeRepository()

        def item_count(self):
            return 1

        def close(self):
            pass

        def save_current_item(self):
            self.saved = True

    screen = EventValidationScreen.__new__(EventValidationScreen)
    screen.session = FakeSession()
    screen.results_path = tmp_path / "event_validation_results.json"

    assert screen.export_results() == [screen.results_path]
    assert read_json(screen.results_path) == {
        "fields": ["Status"],
        "events": {"ev-a": {"answers": ["TP"], "comment": "checked"}},
    }


def test_event_validation_screen_keeps_project_after_completion() -> None:
    screen = EventValidationScreen.__new__(EventValidationScreen)

    assert screen.should_remove_after_completion() is False


def test_event_validation_screen_preserves_blank_answer_selection(qapp) -> None:
    class FakeSession:
        duration_hours = 0.0
        fields = {"Status": {"TP": "green", "FP": "red"}}
        questions = ["Status"]
        answers = {"Status": ""}
        comment = ""

        def item_count(self):
            return 1

        def current_frame(self):
            return np.zeros((10, 10, 3), dtype=np.uint8)

        def status(self):
            return SimpleNamespace(
                item_id=0,
                items_count=1,
                duration_hours=0.0,
                speed_per_hour=0.0,
                processed_count=0,
                view_mode="VIDEO",
                number_of_frames=1,
                current_frame_number=1,
            )

        def update_answer(self, question, answer):
            self.answers[question] = answer

    screen = EventValidationScreen(FakeSession(), Path("event_validation_results.json"))

    combo = screen.findChild(QComboBox)

    assert combo is not None
    assert combo.currentText() == ""


def test_event_validation_screen_has_video_slider_and_playback_controls(qapp) -> None:
    class FakeSession:
        duration_hours = 0.0
        fields = {"Status": {"TP": "green", "FP": "red"}}
        questions = ["Status"]
        answers = {"Status": "TP"}
        comment = ""

        def __init__(self):
            self.frame_number = 0

        def item_count(self):
            return 1

        def current_frame(self):
            return np.zeros((10, 10, 3), dtype=np.uint8)

        def status(self):
            return SimpleNamespace(
                item_id=0,
                items_count=1,
                duration_hours=0.0,
                speed_per_hour=0.0,
                processed_count=0,
                view_mode="VIDEO",
                number_of_frames=5,
                current_frame_number=self.frame_number + 1,
            )

        def update_answer(self, question, answer):
            self.answers[question] = answer

        def update_comment(self, comment):
            self.comment = comment

        def load_video_frame(self, frame_number):
            self.frame_number = frame_number

    session = FakeSession()
    screen = EventValidationScreen(session, Path("event_validation_results.json"))
    slider = screen.findChild(QSlider)
    button_texts = {button.text() for button in screen.findChildren(QPushButton)}

    assert slider is not None
    assert slider.maximum() == 5
    assert {"Play", "Stop"}.issubset(button_texts)

    slider.setValue(3)

    assert session.frame_number == 2
