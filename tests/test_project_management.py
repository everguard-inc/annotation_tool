from pathlib import Path

import pytest

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import BackendError
from annotation_tool.core.models import ProjectData
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
