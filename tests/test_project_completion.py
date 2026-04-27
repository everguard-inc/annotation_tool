from pathlib import Path

import pytest

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import BackendError
from annotation_tool.core.models import ProjectData
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.services.completion_service import CompletionService
from annotation_tool.ui.screens.labeling_screen import LabelingScreen


class CompletionApi:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.completed: list[tuple[str, float]] = []

    def is_available(self) -> bool:
        return self.available

    def complete_task(self, project_uid: str, duration_hours: float) -> None:
        self.completed.append((project_uid, duration_hours))


class FakeFileTransfer:
    def __init__(self) -> None:
        self.uploaded: list[tuple[str, Path]] = []

    def upload(self, uid: str, file_path: Path) -> None:
        self.uploaded.append((uid, file_path))


@pytest.mark.parametrize(
    ("initial_stage", "mode", "expected_stage"),
    [
        (
            AnnotationStage.ANNOTATE,
            AnnotationMode.OBJECT_DETECTION,
            AnnotationStage.SENT_FOR_REVIEW,
        ),
        (
            AnnotationStage.CORRECTION,
            AnnotationMode.OBJECT_DETECTION,
            AnnotationStage.SENT_FOR_REVIEW,
        ),
        (
            AnnotationStage.REVIEW,
            AnnotationMode.OBJECT_DETECTION,
            AnnotationStage.SENT_FOR_CORRECTION,
        ),
        (AnnotationStage.FILTERING, AnnotationMode.FILTERING, AnnotationStage.DONE),
        (
            AnnotationStage.EVENT_VALIDATION,
            AnnotationMode.EVENT_VALIDATION,
            AnnotationStage.DONE,
        ),
    ],
)
def test_completion_service_changes_stage_and_calls_backend(
    tmp_path: Path,
    initial_stage: AnnotationStage,
    mode: AnnotationMode,
    expected_stage: AnnotationStage,
) -> None:
    """Covers FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-096, FR-097, FR-098, FR-166, FR-179, FR-180."""
    project = ProjectData(
        id=12,
        uid="uid-12",
        stage=initial_stage,
        mode=mode,
    )
    repository = ProjectRepository(tmp_path)
    repository.create_local_project(project)

    exported_file = tmp_path / "result.json"
    exported_file.write_text("{}", encoding="utf-8")

    api = CompletionApi(available=True)
    file_transfer = FakeFileTransfer()

    service = CompletionService(
        api_client=api,
        project_repository=repository,
        file_transfer=file_transfer,
    )

    completed = service.complete_current_project(
        project=project,
        duration_hours=2.5,
        export_results=lambda: [exported_file],
        should_remove_after_completion=lambda _: False,
    )

    assert completed.stage is expected_stage
    assert repository.load_state(project.id).stage is expected_stage
    assert api.completed == [("uid-12", 2.5)]
    assert file_transfer.uploaded == [("uid-12", exported_file)]


def test_completion_service_blocks_completion_when_backend_is_unavailable(tmp_path: Path) -> None:
    """Covers FR-032, FR-180."""
    project = ProjectData(
        id=13,
        uid="uid-13",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    repository = ProjectRepository(tmp_path)
    repository.create_local_project(project)

    service = CompletionService(
        api_client=CompletionApi(available=False),
        project_repository=repository,
    )

    with pytest.raises(BackendError, match="Unable to reach"):
        service.complete_current_project(project=project, duration_hours=1.0)

    assert repository.load_state(project.id).stage is AnnotationStage.ANNOTATE


def test_labeling_review_screen_removes_project_when_no_review_labels_remain() -> None:
    class FakeRepository:
        def count_review_labels(self) -> int:
            return 0

    class FakeSession:
        project = ProjectData(
            id=14,
            uid="uid-14",
            stage=AnnotationStage.REVIEW,
            mode=AnnotationMode.OBJECT_DETECTION,
        )
        repository = FakeRepository()

    screen = LabelingScreen.__new__(LabelingScreen)
    screen.session = FakeSession()

    assert screen.should_remove_after_completion() is True
