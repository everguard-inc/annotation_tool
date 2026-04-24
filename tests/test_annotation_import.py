import json
from pathlib import Path

import pytest
from PIL import Image

from annotation_tool.core.exceptions import OperationCancelled
from annotation_tool.core.paths import LabelingPaths
from annotation_tool.core.utils import read_json
from annotation_tool.services.import_export_service import ImportExportService


class FakeFileTransfer:
    def download(self, uid, file_name, save_path, progress=None, should_cancel=None, ignore_404=False):
        save_path.parent.mkdir(parents=True, exist_ok=True)

        if file_name == "meta.json":
            save_path.write_text(
                json.dumps(
                    {
                        "labels": [
                            {"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"}
                        ],
                        "review_labels": [
                            {"name": "Fix", "color": "yellow", "hotkey": "1", "type": "REVIEW_LABEL"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
        elif file_name == "figures.json":
            save_path.write_text(
                json.dumps(
                    {
                        "img1.jpg": {"width": 10, "height": 20, "trash": False, "bboxes": []},
                        "img2.jpg": {"width": 30, "height": 40, "trash": False, "bboxes": []},
                    }
                ),
                encoding="utf-8",
            )
        elif file_name == "review.json":
            save_path.write_text(
                json.dumps({"img2.jpg": [{"label": "Fix", "x": 1, "y": 2}]}),
                encoding="utf-8",
            )
        elif file_name == "archive.zip":
            save_path.write_bytes(b"fake archive")
        else:
            raise AssertionError(f"Unexpected file: {file_name}")

        if progress:
            progress(100, 0, 0, 0)

    def upload(self, uid, file_path):
        raise AssertionError("Upload is not expected here")


class FakeUnzipper:
    def unzip(self, archive_path, output_dir, progress=None, should_cancel=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (10, 20)).save(output_dir / "img1.jpg")
        Image.new("RGB", (30, 40)).save(output_dir / "img2.jpg")

        if progress:
            progress(100, 0, 0, 0)


class RecordingFileTransfer(FakeFileTransfer):
    def __init__(self) -> None:
        self.cancel_callbacks = []

    def download(self, uid, file_name, save_path, progress=None, should_cancel=None, ignore_404=False):
        self.cancel_callbacks.append(should_cancel)
        super().download(
            uid,
            file_name,
            save_path,
            progress=progress,
            should_cancel=should_cancel,
            ignore_404=ignore_404,
        )


class RecordingUnzipper(FakeUnzipper):
    def __init__(self) -> None:
        self.cancel_callbacks = []

    def unzip(self, archive_path, output_dir, progress=None, should_cancel=None):
        self.cancel_callbacks.append(should_cancel)
        super().unzip(
            archive_path,
            output_dir,
            progress=progress,
            should_cancel=should_cancel,
        )


class CancellingFileTransfer:
    def __init__(self) -> None:
        self.downloaded = []

    def download(self, uid, file_name, save_path, progress=None, should_cancel=None, ignore_404=False):
        self.downloaded.append(file_name)
        if should_cancel is not None and should_cancel():
            return
        raise AssertionError("Cancellation should stop before writing files.")

    def upload(self, uid, file_path):
        raise AssertionError("Upload is not expected here")


def test_labeling_project_import_downloads_files_unpacks_images_and_builds_cache(
    data_dir: Path,
    labeling_project,
) -> None:
    """Covers FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, FR-055, FR-056, FR-057, FR-058, FR-059, FR-060, FR-061, FR-062."""
    service = ImportExportService(
        data_dir=data_dir,
        file_transfer=FakeFileTransfer(),
        unzipper=FakeUnzipper(),
    )

    service.import_labeling_project(labeling_project)

    paths = LabelingPaths(data_dir, labeling_project.id)
    cache = read_json(paths.cache_path)

    assert paths.meta_path.exists()
    assert paths.figures_path.exists()
    assert paths.review_path.exists()
    assert (paths.images_dir / "img1.jpg").exists()
    assert (paths.images_dir / "img2.jpg").exists()

    assert [item["name"] for item in cache["items"]] == ["img1.jpg", "img2.jpg"]
    assert cache["items"][0]["requires_annotation"] is False
    assert cache["items"][1]["requires_annotation"] is True
    assert any(label["name"] == "blur" for label in cache["labels"])
    assert cache["review"]["img2.jpg"][0]["label"] == "Fix"


def test_labeling_project_import_forwards_cancellation_to_download_and_unzip(
    data_dir: Path,
    labeling_project,
) -> None:
    file_transfer = RecordingFileTransfer()
    unzipper = RecordingUnzipper()
    service = ImportExportService(
        data_dir=data_dir,
        file_transfer=file_transfer,
        unzipper=unzipper,
    )

    def should_cancel() -> bool:
        return False

    service.import_labeling_project(labeling_project, should_cancel=should_cancel)

    assert file_transfer.cancel_callbacks
    assert all(callback is should_cancel for callback in file_transfer.cancel_callbacks)
    assert unzipper.cancel_callbacks == [should_cancel]


def test_labeling_project_import_aborts_when_cancellation_is_requested(
    data_dir: Path,
    labeling_project,
) -> None:
    file_transfer = CancellingFileTransfer()
    service = ImportExportService(
        data_dir=data_dir,
        file_transfer=file_transfer,
        unzipper=FakeUnzipper(),
    )

    with pytest.raises(OperationCancelled):
        service.import_labeling_project(labeling_project, should_cancel=lambda: True)

    assert file_transfer.downloaded == ["meta.json"]
