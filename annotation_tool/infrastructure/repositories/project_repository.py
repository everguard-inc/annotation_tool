from pathlib import Path

from annotation_tool.core.models import ProjectData


class ProjectRepository:
    def __init__(self, data_dir: Path) -> None:
        ...

    def list_local_projects(self, include_broken: bool = False) -> list[ProjectData]:
        ...

    def load_state(self, project_id: int) -> ProjectData:
        ...

    def save_state(self, project: ProjectData) -> None:
        ...

    def is_valid(self, project_id: int) -> bool:
        ...

    def remove_local_project(self, project_id: int) -> None:
        ...
