from annotation_tool.core.exceptions import BackendError
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import ProjectPaths
from annotation_tool.infrastructure.api_client import ApiClient
from annotation_tool.infrastructure.file_transfer import CancelCallback, ProgressCallback
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.services.import_export_service import ImportExportService
from annotation_tool.services.session_state import SessionStateStore


class ProjectService:
    def __init__(
        self,
        api_client: ApiClient,
        project_repository: ProjectRepository,
        import_export_service: ImportExportService | None = None,
    ) -> None:
        self.api_client = api_client
        self.project_repository = project_repository
        self.import_export_service = import_export_service

    def get_available_projects(self) -> list[ProjectData]:
        try:
            return self.api_client.get_projects()
        except BackendError:
            return self.get_local_projects()

    def get_projects_from_backend(self, only_assigned_to_user: bool = True) -> list[ProjectData]:
        return self.api_client.get_projects(only_assigned_to_user=only_assigned_to_user)

    def get_local_projects(self, include_broken: bool = False) -> list[ProjectData]:
        return self.project_repository.list_local_projects(include_broken=include_broken)

    def download_project(
        self,
        project: ProjectData,
        progress: ProgressCallback | None = None,
        should_cancel: CancelCallback | None = None,
    ) -> None:
        paths = ProjectPaths(self.project_repository.data_dir, project.id)
        project_dir_existed = paths.project_dir.exists()
        self.project_repository.create_local_project(project)

        if self.import_export_service is not None:
            try:
                self.import_export_service.import_project(
                    project, progress=progress, should_cancel=should_cancel
                )
            except Exception:
                if not project_dir_existed:
                    self.project_repository.remove_local_project(project.id)
                raise

    def open_project(
        self,
        project: ProjectData,
        progress: ProgressCallback | None = None,
        should_cancel: CancelCallback | None = None,
    ) -> ProjectData:
        if not self.project_repository.is_valid(project.id):
            self.download_project(
                project, progress=progress, should_cancel=should_cancel
            )
        elif self.project_repository.load_state(project.id).stage != project.stage:
            if self.import_export_service is not None:
                self.import_export_service.import_project(
                    project, progress=progress, should_cancel=should_cancel
                )
            paths = ProjectPaths(self.project_repository.data_dir, project.id)
            SessionStateStore(paths.runtime_state_path).reset()

        self.project_repository.configure_database(project.id)
        self.project_repository.save_state(project)
        return project

    def overwrite_annotations(
        self,
        project: ProjectData,
        progress: ProgressCallback | None = None,
        should_cancel: CancelCallback | None = None,
    ) -> None:
        if self.import_export_service is None:
            return
        self.import_export_service.overwrite_annotations(
            project, progress=progress, should_cancel=should_cancel
        )

    def remove_project(self, project_id: int) -> None:
        self.project_repository.remove_local_project(project_id)

    def remove_completed_local_projects(self) -> list[int]:
        projects = self.api_client.get_projects(only_assigned_to_user=False)
        active_uids = {project.uid for project in projects if project.uid is not None}
        return self.project_repository.remove_projects_not_in(active_uids)
