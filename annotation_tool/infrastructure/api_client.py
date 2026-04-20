from annotation_tool.core.models import ProjectData
from annotation_tool.core.enums import AnnotationMode, AnnotationStage


class ApiClient:
    def __init__(self, api_url: str, token: str) -> None:
        ...

    def get_projects(self, only_assigned_to_user: bool = True) -> list[ProjectData]:
        ...

    def get_project_data(self, project_uid: str) -> tuple[AnnotationStage, AnnotationMode]:
        ...

    def complete_task(self, project_uid: str, duration_hours: float) -> None:
        ...

    def is_available(self) -> bool:
        ...
