import pytest

from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.utils import read_json, write_json
from annotation_tool.services.import_export_service import ImportExportService
from annotation_tool.ui.screens.filtering_screen import FilteringScreen


class UnusedFileTransfer:
    def download(self, *args, **kwargs):
        raise AssertionError("Download is not expected here.")

    def upload(self, *args, **kwargs):
        raise AssertionError("Upload is not expected here.")


def test_selected_frames_are_exported_and_filtering_overwrite_is_blocked(
    data_dir,
    filtering_project,
    filtering_paths,
) -> None:
    """Covers FR-149, FR-164, FR-165, FR-166, FR-167."""
    write_json(
        filtering_paths.cache_path,
        {
            "labels": [{"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"}],
            "items": [
                {"item_id": 2, "name": None, "selected": True},
                {"item_id": 0, "name": "a.jpg", "selected": True},
                {"item_id": 1, "name": "b.jpg", "selected": False},
            ],
        },
    )

    service = ImportExportService(data_dir=data_dir, file_transfer=UnusedFileTransfer())

    selected_path = service.export_selected_frames(filtering_project)

    assert read_json(selected_path) == {"names": ["a.jpg"], "ids": [2]}

    with pytest.raises(UserVisibleError, match="Unable to overwrite annotations"):
        service.overwrite_annotations(filtering_project)


def test_filtering_screen_export_results_writes_selected_frames(tmp_path) -> None:
    """Completion calls the screen export hook, so it must generate the upload file."""

    class FakeRepository:
        def __init__(self) -> None:
            self.flushed = False

        def list_items(self):
            return [
                {"item_id": 2, "name": None, "selected": True},
                {"item_id": 0, "name": "a.jpg", "selected": True},
                {"item_id": 1, "name": "b.jpg", "selected": False},
            ]

        def flush(self) -> None:
            self.flushed = True

    class FakeSession:
        def __init__(self) -> None:
            self.repository = FakeRepository()
            self.saved = False

        def save_current_item(self) -> None:
            self.saved = True

    screen = FilteringScreen.__new__(FilteringScreen)
    screen.session = FakeSession()
    screen.selected_frames_path = tmp_path / "selected_frames.json"

    result = screen.export_results()

    assert result == [screen.selected_frames_path]
    assert read_json(screen.selected_frames_path) == {"names": ["a.jpg"], "ids": [2]}
    assert screen.session.saved is True
    assert screen.session.repository.flushed is True


def test_filtering_screen_removes_project_after_completion() -> None:
    screen = FilteringScreen.__new__(FilteringScreen)

    assert screen.should_remove_after_completion() is True
