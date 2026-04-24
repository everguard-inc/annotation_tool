"""Download-and-overwrite-annotations pipeline tests.

Covers FR-066, FR-067, FR-068, FR-069. Drives
MainWindow.overwrite_annotations() through the expected sequence:
reachability check → confirmation prompt → service call → current-item
refresh. Uses MagicMocks for the outbound services.
"""

from pathlib import Path
from unittest.mock import MagicMock

from PySide6.QtWidgets import QMessageBox

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui import main_window as main_window_module
from annotation_tool.ui.main_window import MainWindow


def _sample_project() -> ProjectData:
    return ProjectData(
        id=7,
        uid="uid-7",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )


def _make_window(
    valid_settings_file: Path, monkeypatch
) -> tuple[MainWindow, list, list]:
    window = MainWindow(SettingsStore(valid_settings_file))
    window.current_project = _sample_project()
    window.current_screen = MagicMock()
    window.current_screen.session.current_item_id.return_value = 3

    window.api_client = MagicMock()
    window.project_service = MagicMock()

    info_calls: list[tuple[str, str]] = []
    error_calls: list[str] = []

    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "information",
        lambda parent, title, text, *a, **kw: info_calls.append((title, text)),
    )
    monkeypatch.setattr(
        main_window_module.ErrorDialog,
        "show_error",
        staticmethod(lambda message, parent=None: error_calls.append(message)),
    )

    class FakeProgress:
        def update_progress(self, *a, **kw):
            pass

        def should_cancel(self):
            return False

        def mark_complete(self):
            pass

    monkeypatch.setattr(window, "_progress", lambda title: FakeProgress())

    return window, info_calls, error_calls


def test_overwrite_aborts_when_backend_not_reachable(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    """Covers FR-067. The reachability check must block everything downstream."""
    window, info_calls, error_calls = _make_window(valid_settings_file, monkeypatch)
    window.api_client.is_available.return_value = False

    question_calls: list = []
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "question",
        lambda *a, **kw: question_calls.append(a) or QMessageBox.StandardButton.Yes,
    )

    window.overwrite_annotations()

    assert window.api_client.is_available.called
    assert question_calls == []
    window.project_service.overwrite_annotations.assert_not_called()
    assert error_calls == [
        "Backend is not reachable. Cannot download and overwrite annotations."
    ]
    assert info_calls == []


def test_overwrite_aborts_when_user_declines_confirmation(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    """Covers FR-068. If the user says No, nothing is downloaded."""
    window, info_calls, error_calls = _make_window(valid_settings_file, monkeypatch)
    window.api_client.is_available.return_value = True
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "question",
        lambda *a, **kw: QMessageBox.StandardButton.No,
    )

    window.overwrite_annotations()

    window.project_service.overwrite_annotations.assert_not_called()
    window.current_screen.reload_current_annotations.assert_not_called()
    assert info_calls == []
    assert error_calls == []


def test_overwrite_runs_service_and_refreshes_current_item_on_accept(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    """Covers FR-066, FR-068, FR-069. Confirmation → service call →
    current item reload on the screen via the non-saving reload path
    (must not call go_to_id, which would persist stale in-memory edits
    over the freshly downloaded cache)."""
    window, info_calls, error_calls = _make_window(valid_settings_file, monkeypatch)
    window.api_client.is_available.return_value = True
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "question",
        lambda *a, **kw: QMessageBox.StandardButton.Yes,
    )

    window.overwrite_annotations()

    window.project_service.overwrite_annotations.assert_called_once()
    called_project = window.project_service.overwrite_annotations.call_args.args[0]
    assert called_project.id == 7

    window.current_screen.reload_current_annotations.assert_called_once_with()
    window.current_screen.go_to_id.assert_not_called()

    assert info_calls == [("Success", "Annotations overwritten.")]
    assert error_calls == []
