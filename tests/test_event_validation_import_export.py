import json
from pathlib import Path

import pytest

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import EventValidationPaths
from annotation_tool.core.utils import read_json
from annotation_tool.services.import_export_service import ImportExportService


class FakeTransfer:
    def __init__(self, files: dict[str, object]) -> None:
        self.files = files
        self.downloaded = []

    def download(
        self,
        uid,
        file_name,
        save_path,
        progress=None,
        should_cancel=None,
        ignore_404=False,
    ):
        self.downloaded.append(file_name)
        data = self.files.get(file_name)
        if data is None and ignore_404:
            return
        if isinstance(data, bytes):
            save_path.write_bytes(data)
        else:
            save_path.write_text(json.dumps(data), encoding="utf-8")

    def upload(self, uid, file_path):
        raise AssertionError("Upload not used in this test")


class FakeUnzipper:
    def unzip(
        self,
        archive_path: Path,
        output_dir: Path,
        progress=None,
        should_cancel=None,
    ):
        videos = output_dir / "videos"
        videos.mkdir(parents=True, exist_ok=True)
        (videos / "ev-a.mp4").write_bytes(b"fake")


def test_import_event_validation_project_builds_cache(data_dir: Path) -> None:
    """Pins Tk import shape:
    - archive.zip extracts into project root and provides top-level videos/
    - meta.json is a list of question/answers/colors dictionaries
    - prior results fields are a list of question names
    """
    project = ProjectData(
        id=44,
        uid="uid-44",
        stage=AnnotationStage.EVENT_VALIDATION,
        mode=AnnotationMode.EVENT_VALIDATION,
    )
    service = ImportExportService(
        data_dir,
        FakeTransfer(
            {
                "archive.zip": b"archive",
                "meta.json": [
                    {
                        "question": "Status",
                        "answers": ["TP", "FP"],
                        "colors": ["green", "red"],
                    }
                ],
                "event_validation_results.json": {
                    "fields": ["Status"],
                    "events": {"ev-a": {"answers": ["TP"], "comment": "ok"}},
                },
            }
        ),
        FakeUnzipper(),
    )

    service.import_project(project)

    cache = read_json(EventValidationPaths(data_dir, 44).cache_path)
    assert cache["fields"] == {"Status": {"TP": "green", "FP": "red"}}
    assert cache["events"]["ev-a"] == {"answers": ["TP"], "comment": "ok"}


def test_import_event_validation_rejects_prior_results_with_mismatched_fields(
    data_dir: Path,
) -> None:
    project = ProjectData(
        id=44,
        uid="uid-44",
        stage=AnnotationStage.EVENT_VALIDATION,
        mode=AnnotationMode.EVENT_VALIDATION,
    )
    service = ImportExportService(
        data_dir,
        FakeTransfer(
            {
                "archive.zip": b"archive",
                "meta.json": [
                    {
                        "question": "Status",
                        "answers": ["TP", "FP"],
                        "colors": ["green", "red"],
                    }
                ],
                "event_validation_results.json": {
                    "fields": ["Different"],
                    "events": {"ev-a": {"answers": ["TP"], "comment": "old"}},
                },
            }
        ),
        FakeUnzipper(),
    )

    with pytest.raises(UserVisibleError, match="Validation rules are different"):
        service.import_project(project)


def test_export_event_validation_results_writes_backend_shape(
    data_dir: Path,
) -> None:
    """Pins Tk export contract from EventValidationIO._export_event_validation_results:
    fields is list(fields.keys()), while answer/color mappings stay in meta/cache.
    """
    project = ProjectData(
        id=45,
        uid="uid-45",
        stage=AnnotationStage.EVENT_VALIDATION,
        mode=AnnotationMode.EVENT_VALIDATION,
    )
    paths = EventValidationPaths(data_dir, 45)
    paths.ensure_project_dir()
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {"ev-a": {"answers": ["FP"], "comment": "bad"}},
            }
        ),
        encoding="utf-8",
    )
    service = ImportExportService(data_dir, FakeTransfer({}))

    result = service.export_results(project)

    assert result == [paths.results_path]
    assert read_json(paths.results_path) == {
        "fields": ["Status"],
        "events": {"ev-a": {"answers": ["FP"], "comment": "bad"}},
    }
