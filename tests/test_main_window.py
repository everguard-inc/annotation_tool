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


def test_update_tool_runs_git_pull_and_shows_result(
    qapp,
    valid_settings_file: Path,
    monkeypatch,
) -> None:
    window = MainWindow(SettingsStore(valid_settings_file))
    shown_messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda parent, title, message: shown_messages.append(message),
    )

    def fake_run(command, capture_output, text):
        assert command[0] == "git"
        assert command[1] == "-C"
        assert command[-1] == "pull"
        return subprocess.CompletedProcess(command, 0, stdout="Updating abc..def\n", stderr="")

    monkeypatch.setattr("annotation_tool.ui.main_window.subprocess.run", fake_run)

    window.update_tool()

    assert shown_messages
    assert "Success" in shown_messages[0]
    assert "Re-open the tool" in shown_messages[0]
