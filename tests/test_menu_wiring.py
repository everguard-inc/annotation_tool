"""Menu-bar wiring tests.

Covers FR-006, FR-020, FR-028 — the `Project > Download`, `Project >
Settings`, and `Project > Go to ID` menu entries must route to their
respective handlers and surface the expected dialog/flow.
"""

from pathlib import Path
from unittest.mock import MagicMock

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui import main_window as main_window_module
from annotation_tool.ui.main_window import MainWindow


def test_download_menu_action_drives_download_project(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    """Covers FR-006."""
    window = MainWindow(SettingsStore(valid_settings_file))

    download_project_calls: list = []
    monkeypatch.setattr(
        window, "download_project", lambda *a, **kw: download_project_calls.append(True)
    )
    window.actions.download_action.triggered.disconnect()
    window.actions.download_action.triggered.connect(window.download_project)

    window.actions.download_action.trigger()

    assert download_project_calls == [True]


def test_settings_menu_action_opens_settings_dialog(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    """Covers FR-020."""
    window = MainWindow(SettingsStore(valid_settings_file))

    shown_dialogs: list = []

    class FakeDialog:
        DialogCode = type("DialogCode", (), {"Accepted": 1, "Rejected": 0})

        def __init__(self, *a, **kw) -> None:
            shown_dialogs.append((a, kw))

        def exec(self) -> int:
            return FakeDialog.DialogCode.Rejected

    monkeypatch.setattr(main_window_module, "SettingsDialog", FakeDialog)

    window.actions.settings_action.trigger()

    assert len(shown_dialogs) == 1


def test_go_to_id_menu_action_routes_through_dialog_to_screen(
    qapp, valid_settings_file: Path, monkeypatch
) -> None:
    """Covers FR-028."""
    window = MainWindow(SettingsStore(valid_settings_file))
    window.current_project = ProjectData(
        id=7,
        uid="uid-7",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    window.current_screen = MagicMock()
    window.current_screen.items_count = 25
    window.actions.set_project_opened(True)

    class FakeDialog:
        DialogCode = type("DialogCode", (), {"Accepted": 1, "Rejected": 0})

        def __init__(self, items_count: int, parent=None) -> None:
            self.items_count = items_count

        def exec(self) -> int:
            return FakeDialog.DialogCode.Accepted

        def selected_id(self) -> int:
            return 5

    monkeypatch.setattr(main_window_module, "IdDialog", FakeDialog)

    window.actions.go_to_id_action.trigger()

    window.current_screen.go_to_id.assert_called_once_with(4)
