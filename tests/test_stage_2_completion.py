from pathlib import Path

import pytest

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import BackendError
from annotation_tool.core.models import ProjectData
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.services.completion_service import CompletionService


class CompletionApi:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.completed: list[tuple[str, float]] = []

    def is_available(self) -> bool:
        return self.available

    def complete_task(self, project_uid: str, duration_hours: float) -> None:
        self.completed.append((project_uid, duration_hours))


@pytest.mark.parametrize(
    ("initial_stage", "expected_stage"),
    [
        (AnnotationStage.ANNOTATE, AnnotationStage.SENT_FOR_REVIEW),
        (AnnotationStage.CORRECTION, AnnotationStage.SENT_FOR_REVIEW),
        (AnnotationStage.REVIEW, AnnotationStage.SENT_FOR_CORRECTION),
        (AnnotationStage.FILTERING, AnnotationStage.DONE),
    ],
)
def test_completion_service_changes_stage_and_calls_backend(
    tmp_path: Path,
    initial_stage: AnnotationStage,
    expected_stage: AnnotationStage,
) -> None:
    """Covers FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-096, FR-097, FR-098, FR-166, FR-179, FR-180."""
    project = ProjectData(
        id=12,
        uid="uid-12",
        stage=initial_stage,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    repository = ProjectRepository(tmp_path)
    repository.create_local_project(project)

    exported_file = tmp_path / "result.json"
    exported_file.write_text("{}", encoding="utf-8")

    uploaded: list[tuple[str, Path]] = []
    api = CompletionApi(available=True)
    service = CompletionService(
        api,
        repository,
        upload_file=lambda uid, path: uploaded.append((uid, path)),
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
    assert uploaded == [("uid-12", exported_file)]


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

    service = CompletionService(CompletionApi(available=False), repository)

    with pytest.raises(BackendError, match="Unable to reach"):
        service.complete_current_project(project=project, duration_hours=1.0)

    assert repository.load_state(project.id).stage is AnnotationStage.ANNOTATE
