"""Error-dialog shape and data_dir-failure tests.

Covers FR-174 (copyable error window), FR-175 (scrollable +
Close button), and FR-025 (data_dir failure path shows error
window and clears the invalid value).
"""

import json
from pathlib import Path

import pytest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox, QTextEdit

from annotation_tool.core.exceptions import SettingsError
from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui.dialogs.error_dialog import ErrorDialog


def test_error_dialog_surfaces_copyable_readonly_text(qapp) -> None:
    """Covers FR-174. The error window must present the message inside a
    selectable / copyable read-only surface so users can hand the text to
    support, not a plain QLabel."""
    message = "Something broke\nTraceback (most recent call last):\n  File ..."
    dialog = ErrorDialog(message)

    assert isinstance(dialog.text, QTextEdit)
    assert dialog.text.isReadOnly() is True
    assert dialog.text.toPlainText() == message
    flags = dialog.text.textInteractionFlags()
    assert flags & Qt.TextInteractionFlag.TextSelectableByMouse


def test_error_dialog_has_scrollable_body_and_close_button(qapp) -> None:
    """Covers FR-175. The dialog must be scrollable (QTextEdit provides its
    own scroll area) and carry a Close button."""
    dialog = ErrorDialog("x")

    button_boxes = dialog.findChildren(QDialogButtonBox)
    assert len(button_boxes) == 1
    standard = button_boxes[0].standardButtons()
    assert standard & QDialogButtonBox.StandardButton.Close

    # The long-message path must not truncate; the text widget owns the
    # scrolling and wraps/overflows rather than clipping the content.
    long_message = "\n".join(f"line {i}" for i in range(200))
    dialog2 = ErrorDialog(long_message)
    assert dialog2.text.toPlainText() == long_message


def test_settings_store_clears_data_dir_and_raises_when_mkdir_fails(
    tmp_path: Path,
) -> None:
    """Covers FR-025. When data_dir cannot be created, SettingsStore must
    clear the stored data_dir value and raise SettingsError."""
    settings_path = tmp_path / "settings.json"

    blocking_file = tmp_path / "blocker.txt"
    blocking_file.write_text("blocks mkdir", encoding="utf-8")
    uncreatable_data_dir = blocking_file / "cannot-create"

    settings_path.write_text(
        json.dumps(
            {
                "general": {
                    "token": {"type": "string", "value": "t"},
                    "api_url": {"type": "string", "value": "https://api"},
                    "file_url": {"type": "string", "value": "https://files"},
                    "data_dir": {"type": "string", "value": str(uncreatable_data_dir)},
                },
                "interface": {},
            }
        ),
        encoding="utf-8",
    )

    store = SettingsStore(settings_path)

    with pytest.raises(SettingsError) as excinfo:
        store.load()

    assert "data_dir" in str(excinfo.value)

    persisted = json.loads(settings_path.read_text(encoding="utf-8"))
    assert persisted["general"]["data_dir"]["value"] == ""
    assert store.has_empty_required_values() is True


def test_main_window_shows_error_dialog_when_data_dir_cannot_be_created(
    qapp, tmp_path: Path, monkeypatch
) -> None:
    """Covers the UI-surface half of FR-025. A MainWindow constructed
    against settings with an uncreatable data_dir must surface the
    ErrorDialog rather than crash, and settings.json must come out
    with data_dir cleared."""
    from annotation_tool.core.settings import SettingsStore
    from annotation_tool.ui import main_window as main_window_module
    from annotation_tool.ui.main_window import MainWindow

    blocking_file = tmp_path / "blocker.txt"
    blocking_file.write_text("blocks mkdir", encoding="utf-8")
    uncreatable_data_dir = blocking_file / "cannot-create"

    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "general": {
                    "token": {"type": "string", "value": "t"},
                    "api_url": {"type": "string", "value": "https://api"},
                    "file_url": {"type": "string", "value": "https://files"},
                    "data_dir": {
                        "type": "string",
                        "value": str(uncreatable_data_dir),
                    },
                },
                "interface": {},
            }
        ),
        encoding="utf-8",
    )

    error_calls: list[str] = []
    monkeypatch.setattr(
        main_window_module.ErrorDialog,
        "show_error",
        staticmethod(lambda message, parent=None: error_calls.append(message)),
    )

    window = MainWindow(SettingsStore(settings_path))

    assert len(error_calls) == 1
    assert "data_dir" in error_calls[0]
    assert window.settings is None
    assert window.project_service is None

    persisted = json.loads(settings_path.read_text(encoding="utf-8"))
    assert persisted["general"]["data_dir"]["value"] == ""
