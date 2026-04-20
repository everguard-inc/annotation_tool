import shutil
from pathlib import Path

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import ProjectPaths
from annotation_tool.core.utils import is_valid_json, read_json, write_json
from annotation_tool.infrastructure.db import Database


class ProjectRepository:
    def __init__(self, data_dir: Path, database: Database | None = None) -> None:
        self.data_dir = data_dir
        self.database = database or Database()

    def list_local_projects(self, include_broken: bool = False) -> list[ProjectData]:
        data_path = self.data_dir / "data"
        if not data_path.exists():
            return []

        projects: list[ProjectData] = []

        for project_dir in sorted(data_path.iterdir()):
            if not project_dir.is_dir():
                continue

            try:
                project_id = int(project_dir.name)
            except ValueError:
                continue

            if self.is_valid(project_id):
                projects.append(self.load_state(project_id))
                continue

            if include_broken:
                projects.append(self._broken_project(project_id))

        return projects

    def load_state(self, project_id: int) -> ProjectData:
        paths = ProjectPaths(self.data_dir, project_id)
        return ProjectData.from_dict(read_json(paths.state_path))

    def save_state(self, project: ProjectData) -> None:
        paths = ProjectPaths(self.data_dir, project.id)
        paths.ensure_project_dir()
        write_json(paths.state_path, project.to_dict())

    def is_valid(self, project_id: int) -> bool:
        paths = ProjectPaths(self.data_dir, project_id)

        return (
            paths.project_dir.exists()
            and paths.state_path.exists()
            and is_valid_json(paths.state_path)
            and paths.db_path.exists()
        )

    def create_local_project(self, project: ProjectData) -> None:
        paths = ProjectPaths(self.data_dir, project.id)
        paths.ensure_project_dir()
        self.save_state(project)
        self.database.configure(paths.db_path)
        self.database.close()

    def configure_database(self, project_id: int) -> None:
        paths = ProjectPaths(self.data_dir, project_id)
        paths.ensure_project_dir()
        self.database.configure(paths.db_path)

    def remove_local_project(self, project_id: int) -> None:
        paths = ProjectPaths(self.data_dir, project_id)
        if paths.project_dir.exists():
            shutil.rmtree(paths.project_dir)

    def remove_projects_not_in(self, active_project_uids: set[str]) -> list[int]:
        removed_ids: list[int] = []

        for project in self.list_local_projects(include_broken=True):
            if project.uid is None or project.uid not in active_project_uids:
                self.remove_local_project(project.id)
                removed_ids.append(project.id)

        return removed_ids

    def _broken_project(self, project_id: int) -> ProjectData:
        paths = ProjectPaths(self.data_dir, project_id)

        if paths.state_path.exists() and is_valid_json(paths.state_path):
            try:
                return ProjectData.from_dict(read_json(paths.state_path))
            except Exception:
                pass

        return ProjectData(
            id=project_id,
            uid=None,
            stage=AnnotationStage.UNKNOWN,
            mode=AnnotationMode.UNKNOWN,
        )
