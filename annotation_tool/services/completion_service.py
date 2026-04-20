from collections.abc import Callable
from pathlib import Path

from annotation_tool.core.enums import AnnotationStage
from annotation_tool.core.exceptions import BackendError, ValidationError
from annotation_tool.core.models import CheckResult, ProjectData
from annotation_tool.core.paths import ProjectPaths
from annotation_tool.infrastructure.api_client import ApiClient
from annotation_tool.infrastructure.file_transfer import FileTransferClient
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.services.import_export_service import ImportExportService
from annotation_tool.services.session_state import SessionStateStore


class CompletionService:
    def __init__(
        self,
        api_client: ApiClient,
        project_repository: ProjectRepository,
        file_transfer: FileTransferClient | None = None,
        import_export_service: ImportExportService | None = None,
    ) -> None:
        self.api_client = api_client
        self.project_repository = project_repository
        self.file_transfer = file_transfer
        self.import_export_service = import_export_service

    def check_before_completion(self) -> CheckResult:
        return CheckResult(ready_to_complete=True)

    def complete_current_project(
        self,
        project: ProjectData,
        duration_hours: float,
        export_results: Callable[[], list[Path]] | None = None,
        should_remove_after_completion: Callable[[ProjectData], bool] | None = None,
    ) -> ProjectData:
        check_result = self.check_before_completion()
        if not check_result.ready_to_complete:
            raise ValidationError(check_result.message)

        if project.uid is None:
            raise ValidationError("Project UID is missing.")

        if not self.api_client.is_available():
            raise BackendError("Unable to reach a web service. Project is not completed.")

        paths_to_upload = self._collect_result_paths(project, export_results)

        for path in paths_to_upload:
            if path.exists() and self.file_transfer is not None:
                self.file_transfer.upload(project.uid, path)

        self.api_client.complete_task(project.uid, duration_hours)

        completed_project = ProjectData(
            id=project.id,
            uid=project.uid,
            stage=self._next_stage(project.stage),
            mode=project.mode,
        )
        self.project_repository.save_state(completed_project)

        paths = ProjectPaths(self.project_repository.data_dir, project.id)
        SessionStateStore(paths.runtime_state_path).reset()

        remove = should_remove_after_completion(completed_project) if should_remove_after_completion else False
        if remove:
            self.project_repository.remove_local_project(project.id)

        return completed_project

    def _collect_result_paths(
        self,
        project: ProjectData,
        export_results: Callable[[], list[Path]] | None,
    ) -> list[Path]:
        result = export_results() if export_results is not None else []

        if not result and self.import_export_service is not None:
            result = self.import_export_service.export_results(project)

        statistics_path = ProjectPaths(self.project_repository.data_dir, project.id).statistics_path
        if statistics_path.exists():
            result.append(statistics_path)

        return result

    def _next_stage(self, stage: AnnotationStage) -> AnnotationStage:
        if stage in {AnnotationStage.ANNOTATE, AnnotationStage.CORRECTION}:
            return AnnotationStage.SENT_FOR_REVIEW

        if stage is AnnotationStage.REVIEW:
            return AnnotationStage.SENT_FOR_CORRECTION

        return AnnotationStage.DONE
