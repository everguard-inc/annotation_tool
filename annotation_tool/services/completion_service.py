from annotation_tool.core.models import CheckResult


class CompletionService:
    def check_before_completion(self) -> CheckResult:
        ...

    def complete_current_project(self) -> None:
        ...
