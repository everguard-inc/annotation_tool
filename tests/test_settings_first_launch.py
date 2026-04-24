from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from annotation_tool.core.exceptions import SettingsError
from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui.dialogs.settings_dialog import SettingsDialog


def test_settings_file_is_created_with_empty_required_values(tmp_path: Path) -> None:
    """Covers FR-022, FR-024."""
    settings_path = tmp_path / "settings.json"

    store = SettingsStore(settings_path)

    assert settings_path.exists()
    assert store.has_empty_required_values()
    assert store.missing_required_values() == [
        "token",
        "api_url",
        "file_url",
        "data_dir",
    ]

    with pytest.raises(SettingsError, match="Missing required settings"):
        store.load()


def test_required_settings_dialog_blocks_save_until_required_fields_are_filled(
    qapp,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Covers FR-022, FR-024."""
    store = SettingsStore(tmp_path / "settings.json")
    warnings = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda parent, title, message: warnings.append((title, message)),
    )

    dialog = SettingsDialog(
        store.draft_settings(),
        required_mode=True,
        missing_fields=store.missing_required_values(),
    )

    dialog.accept()

    assert warnings
    assert "token" in warnings[0][1]
    assert dialog.result() == 0

    dialog.token_input.setText("token")
    dialog.api_url_input.setText("https://api.example.com")
    dialog.file_url_input.setText("https://files.example.com")
    dialog.data_dir_input.setText(str(tmp_path / "data"))

    dialog.accept()

    assert dialog.result() == SettingsDialog.DialogCode.Accepted
