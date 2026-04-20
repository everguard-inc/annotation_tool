import subprocess
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui.main_window import MainWindow


def test_main_window_updates_title_and_project_actions(qapp, valid_settings_file: Path) -> None:
    window = MainWindow(SettingsStore(valid_settings_file))

    window.set_current_project_title(42)

    assert window.windowTitle() == "Project 42"
    assert window.actions.go_to_id_action.isEnabled()
    assert window.actions.complete_action.isEnabled()

    window.set_current_project_title(None)

    assert window.windowTitle() == "Annotation tool"
    assert not window.actions.go_to_id_action.isEnabled()
    assert not window.actions.complete_action.isEnabled()