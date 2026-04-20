import pytest

from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.utils import read_json, write_json
from annotation_tool.services.import_export_service import ImportExportService


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
