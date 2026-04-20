from collections.abc import Callable
from pathlib import Path

from annotation_tool.core.enums import AnnotationStage
from annotation_tool.core.exceptions import BackendError, ValidationError
from annotation_tool.core.models import CheckResult, ProjectData
from annotation_tool.infrastructure.api_client import ApiClient
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository


class CompletionService:
    def __init__(
        self,
        api_client: ApiClient,
        project_repository: ProjectRepository,
        upload_file: Callable[[str, Path], None] | None = None,
    ) -> None:
        self.api_client = api_client
        self.project_repository = project_repository
        self.upload_file = upload_file

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

        result_paths = export_results() if export_results is not None else []

        for path in result_paths:
            if path.exists() and self.upload_file is not None:
                self.upload_file(project.uid, path)

        self.api_client.complete_task(project.uid, duration_hours)

        completed_project = ProjectData(
            id=project.id,
            uid=project.uid,
            stage=self._next_stage(project.stage),
            mode=project.mode,
        )
        self.project_repository.save_state(completed_project)

        remove = should_remove_after_completion(completed_project) if should_remove_after_completion else False
        if remove:
            self.project_repository.remove_local_project(project.id)

        return completed_project

    def _next_stage(self, stage: AnnotationStage) -> AnnotationStage:
        if stage in {AnnotationStage.ANNOTATE, AnnotationStage.CORRECTION}:
            return AnnotationStage.SENT_FOR_REVIEW

        if stage is AnnotationStage.REVIEW:
            return AnnotationStage.SENT_FOR_CORRECTION

        return AnnotationStage.DONE
