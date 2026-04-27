"""Golden labeling completion parity tests.

Tk baseline: origin/main 1dd11801066386f137f64ab2ad028005f325f463.
"""

from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import LabelingPaths, ProjectPaths
from annotation_tool.core.settings import SettingsStore
from annotation_tool.core.utils import write_json
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.services.completion_service import CompletionService
from annotation_tool.services.import_export_service import ImportExportService
from annotation_tool.ui import main_window as main_window_module
from annotation_tool.ui.main_window import MainWindow


class AvailableApi:
    def __init__(self) -> None:
        self.completed = []

    def is_available(self) -> bool:
        return True

    def complete_task(self, project_uid: str, duration_hours: float) -> None:
        self.completed.append((project_uid, duration_hours))


class RecordingTransfer:
    def __init__(self) -> None:
        self.uploaded = []

    def download(self, *args, **kwargs):
        raise AssertionError("download is not expected")

    def upload(self, uid: str, file_path: Path) -> None:
        self.uploaded.append((uid, file_path.name))


class CompletedScreen:
    items_count = 1

    def __init__(self) -> None:
        self.duration_hours = 2.5
        self.saved = 0
        self.closed = 0

    def save(self) -> None:
        self.saved += 1

    def close_screen(self) -> None:
        self.closed += 1
        raise AssertionError("completion close must not call normal close_screen")

    def deleteLater(self) -> None:
        pass

    def export_results(self) -> list[Path]:
        return []

    def should_remove_after_completion(self) -> bool:
        return True


def test_review_completion_does_not_repersist_state_or_recreate_removed_project(
    qapp,
    valid_settings_file: Path,
    monkeypatch,
) -> None:
    settings = SettingsStore(valid_settings_file).load()
    project = ProjectData(
        id=601,
        uid="uid-601",
        stage=AnnotationStage.REVIEW,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    repository = ProjectRepository(settings.data_dir)
    repository.create_local_project(project)
    paths = LabelingPaths(settings.data_dir, project.id)
    write_json(paths.cache_path, {"figures": {}, "review": {}})
    write_json(
        paths.runtime_state_path,
        {"item_id": 4, "duration_hours": 9.0, "processed_item_ids": [1, 2, 3]},
    )

    transfer = RecordingTransfer()
    api = AvailableApi()
    window = MainWindow(SettingsStore(valid_settings_file))
    window.current_project = project
    window.current_screen = CompletedScreen()
    window.completion_service = CompletionService(
        api_client=api,
        project_repository=repository,
        file_transfer=transfer,
        import_export_service=ImportExportService(settings.data_dir, transfer),
    )
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "information",
        lambda *args, **kwargs: None,
    )

    window.complete_project()

    assert api.completed == [("uid-601", 2.5)]
    assert transfer.uploaded == [("uid-601", "review.json")]
    assert window.current_project is None
    assert window.current_screen is None
    assert not ProjectPaths(settings.data_dir, project.id).project_dir.exists()
