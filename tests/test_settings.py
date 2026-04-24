import json
from pathlib import Path

import pytest

from annotation_tool.core.exceptions import SettingsError
from annotation_tool.core.settings import AppSettings, SettingsStore


def test_settings_store_loads_values_and_creates_data_dir(
    valid_settings_file: Path,
) -> None:
    """Covers FR-021, FR-022."""
    store = SettingsStore(valid_settings_file)

    settings = store.load()

    assert settings.token == "token-123"
    assert settings.api_url == "https://api.example.com"
    assert settings.file_url == "https://files.example.com"
    assert settings.data_dir.exists()
    assert settings.bbox_line_width == 3.0
    assert settings.keypoint_handler_size == 5.0


def test_settings_store_detects_empty_required_values(tmp_path: Path) -> None:
    """Covers FR-024."""
    settings_path = tmp_path / "settings.json"
    store = SettingsStore(settings_path)

    assert store.has_empty_required_values() is True

    with pytest.raises(SettingsError):
        store.load()


def test_settings_store_saves_settings_and_removes_url_trailing_slashes(
    tmp_path: Path,
) -> None:
    """Covers FR-021, FR-022."""
    settings_path = tmp_path / "settings.json"
    data_dir = tmp_path / "data"
    store = SettingsStore(settings_path)

    store.save(
        AppSettings(
            token="abc",
            api_url="https://api.example.com/",
            file_url="https://files.example.com/",
            data_dir=data_dir,
            bbox_line_width=3.0,
            cursor_proximity_threshold=3.0,
            objects_opacity=0.9,
            color_fill_opacity=0.1,
            bbox_handler_size=3.0,
            keypoint_handler_size=5.0,
        )
    )

    loaded = store.load()
    raw = json.loads(settings_path.read_text(encoding="utf-8"))

    assert loaded.api_url == "https://api.example.com"
    assert loaded.file_url == "https://files.example.com"
    assert loaded.data_dir == data_dir
    assert raw["general"]["token"]["value"] == "abc"
    assert data_dir.exists()


def test_settings_store_round_trips_all_six_interface_fields(tmp_path: Path) -> None:
    """Covers FR-023. All six interface parameters (bbox_line_width,
    cursor_proximity_threshold, objects_opacity, color_fill_opacity,
    bbox_handler_size, keypoint_handler_size) must survive a save + reload."""
    settings_path = tmp_path / "settings.json"
    data_dir = tmp_path / "data"
    store = SettingsStore(settings_path)

    store.save(
        AppSettings(
            token="abc",
            api_url="https://api.example.com",
            file_url="https://files.example.com",
            data_dir=data_dir,
            bbox_line_width=4.25,
            cursor_proximity_threshold=7.5,
            objects_opacity=0.77,
            color_fill_opacity=0.33,
            bbox_handler_size=2.5,
            keypoint_handler_size=6.25,
        )
    )

    loaded = store.load()

    assert loaded.bbox_line_width == 4.25
    assert loaded.cursor_proximity_threshold == 7.5
    assert loaded.objects_opacity == 0.77
    assert loaded.color_fill_opacity == 0.33
    assert loaded.bbox_handler_size == 2.5
    assert loaded.keypoint_handler_size == 6.25

    raw = json.loads(settings_path.read_text(encoding="utf-8"))
    interface = raw["interface"]
    assert interface["bbox_line_width"]["value"] == 4.25
    assert interface["cursor_proximity_threshold"]["value"] == 7.5
    assert interface["objects_opacity"]["value"] == 0.77
    assert interface["color_fill_opacity"]["value"] == 0.33
    assert interface["bbox_handler_size"]["value"] == 2.5
    assert interface["keypoint_handler_size"]["value"] == 6.25
