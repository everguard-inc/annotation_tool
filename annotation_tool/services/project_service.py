from annotation_tool.core.models import ProjectData


class ProjectService:
    def get_available_projects(self) -> list[ProjectData]:
        ...

    def get_local_projects(self, include_broken: bool = False) -> list[ProjectData]:
        ...

    def download_project(self, project: ProjectData) -> None:
        ...

    def open_project(self, project: ProjectData) -> None:
        ...

    def remove_project(self, project_id: int) -> None:
        ...

    def remove_completed_local_projects(self) -> None:
        ...
