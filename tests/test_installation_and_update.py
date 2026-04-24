import subprocess
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui.main_window import MainWindow


def test_linux_installer_creates_venv_installs_requirements_and_desktop_shortcut() -> (
    None
):
    """Covers FR-002."""
    script = Path("install_linux.sh").read_text(encoding="utf-8")

    assert "python3" in script
    assert "venv" in script
    assert "pip install -r" in script
    assert "requirements.txt" in script
    assert "Labeling.desktop" in script
    assert (
        'python" -m annotation_tool' in script
        or 'python" -m annotation_tool' in script.replace("\\", "")
    )


def test_update_tool_pulls_code_installs_requirements_and_refreshes_shortcut(
    qapp,
    valid_settings_file: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Covers FR-026, FR-027."""
    window = MainWindow(SettingsStore(valid_settings_file))

    commands = []
    messages = []

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda parent, title, message: messages.append(message),
    )
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    desktop = tmp_path / "Desktop"
    desktop.mkdir()

    def fake_run(command, capture_output, text):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr("annotation_tool.ui.main_window.subprocess.run", fake_run)

    window.update_tool()

    assert commands[0][0] == "git"
    assert commands[0][-1] == "pull"
    assert commands[1][-3:] == ["install", "--upgrade", "pip"]
    assert commands[2][-3:] == [
        "install",
        "-r",
        str(Path(__file__).resolve().parents[1] / "requirements.txt"),
    ]
    assert (desktop / "Labeling.desktop").exists()
    assert "-m annotation_tool" in (desktop / "Labeling.desktop").read_text(
        encoding="utf-8"
    )
    assert "Success" in messages[-1]
