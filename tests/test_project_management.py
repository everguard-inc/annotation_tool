from pathlib import Path

import pytest

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import BackendError, OperationCancelled
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import ProjectPaths
from annotation_tool.core.utils import read_json, write_json
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.services.project_service import ProjectService


class FailingApi:
    def get_projects(self, only_assigned_to_user: bool = True):
        raise BackendError("backend unavailable")


class StaticApi:
    def __init__(self, projects: list[ProjectData]) -> None:
        self.projects = projects
        self.only_assigned_values: list[bool] = []

    def get_projects(self, only_assigned_to_user: bool = True):
        self.only_assigned_values.append(only_assigned_to_user)
        return self.projects


def test_project_repository_creates_valid_local_project(tmp_path: Path, sample_project: ProjectData) -> None:
    """Covers FR-011, FR-012, FR-013, FR-014, FR-015, FR-016."""
    repository = ProjectRepository(tmp_path)

    repository.create_local_project(sample_project)

    project_dir = tmp_path / "data" / "00007"
    assert project_dir.exists()
    assert (project_dir / "state.json").exists()
    assert (project_dir / "db.sqlite").exists()
    assert repository.is_valid(sample_project.id)

    loaded = repository.load_state(sample_project.id)
    assert loaded == sample_project


def test_project_service_falls_back_to_local_projects_when_backend_fails(
    tmp_path: Path,
    sample_project: ProjectData,
) -> None:
    """Covers FR-004, FR-005, FR-176, FR-177, FR-178."""
    repository = ProjectRepository(tmp_path)
    repository.create_local_project(sample_project)

    service = ProjectService(FailingApi(), repository)

    projects = service.get_available_projects()

    assert projects == [sample_project]


def test_project_service_removes_local_projects_not_active_on_backend(tmp_path: Path) -> None:
    """Covers FR-017, FR-018, FR-019, FR-181."""
    active_project = ProjectData(
        id=1,
        uid="active-uid",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    stale_project = ProjectData(
        id=2,
        uid="stale-uid",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )

    repository = ProjectRepository(tmp_path)
    repository.create_local_project(active_project)
    repository.create_local_project(stale_project)

    service = ProjectService(StaticApi([active_project]), repository)

    removed_ids = service.remove_completed_local_projects()

    assert removed_ids == [stale_project.id]
    assert repository.is_valid(active_project.id)
    assert not (tmp_path / "data" / "00002").exists()


def test_project_service_opens_project_and_persists_latest_state(tmp_path: Path) -> None:
    """Covers FR-008, FR-183, FR-184, FR-185."""
    original = ProjectData(
        id=9,
        uid="uid-9",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    updated = ProjectData(
        id=9,
        uid="uid-9",
        stage=AnnotationStage.REVIEW,
        mode=AnnotationMode.OBJECT_DETECTION,
    )

    repository = ProjectRepository(tmp_path)
    service = ProjectService(StaticApi([updated]), repository)

    service.download_project(original)
    opened = service.open_project(updated)

    assert opened == updated
    assert repository.load_state(9).stage is AnnotationStage.REVIEW
    assert repository.is_valid(9)


def test_project_service_reinitializes_valid_project_when_stage_changes(
    tmp_path: Path,
) -> None:
    original = ProjectData(
        id=9,
        uid="uid-9",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    updated = ProjectData(
        id=9,
        uid="uid-9",
        stage=AnnotationStage.REVIEW,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    paths = ProjectPaths(tmp_path, 9)
    repository = ProjectRepository(tmp_path)
    repository.create_local_project(original)
    write_json(
        paths.runtime_state_path,
        {
            "item_id": 7,
            "duration_hours": 2.0,
            "processed_item_ids": [1, 3],
        },
    )

    class FakeImportExportService:
        def __init__(self):
            self.imported = []
            self.overwrite_calls = []

        def import_project(self, project, progress=None, should_cancel=None):
            self.imported.append(project)

        def overwrite_annotations(self, project, progress=None, should_cancel=None):
            self.overwrite_calls.append(project)

    import_export_service = FakeImportExportService()
    service = ProjectService(
        StaticApi([updated]),
        repository,
        import_export_service=import_export_service,
    )

    opened = service.open_project(updated)

    assert opened == updated
    assert import_export_service.imported == [updated]
    assert import_export_service.overwrite_calls == []
    assert repository.load_state(9).stage is AnnotationStage.REVIEW
    assert read_json(paths.runtime_state_path)["item_id"] == 0
    assert read_json(paths.runtime_state_path)["duration_hours"] == 0.0
    assert read_json(paths.runtime_state_path)["processed_item_ids"] == []


def test_project_service_removes_fresh_local_project_when_download_is_cancelled(
    tmp_path: Path,
) -> None:
    project = ProjectData(
        id=9,
        uid="uid-9",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )

    class CancellingImportExportService:
        def import_project(self, project, progress=None, should_cancel=None):
            raise OperationCancelled("cancelled")

    repository = ProjectRepository(tmp_path)
    service = ProjectService(
        StaticApi([project]),
        repository,
        import_export_service=CancellingImportExportService(),
    )

    with pytest.raises(OperationCancelled):
        service.download_project(project)

    assert not repository.is_valid(project.id)
    assert not (tmp_path / "data" / "00009").exists()
