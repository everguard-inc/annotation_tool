from pathlib import Path

from annotation_tool.core.enums import AnnotationStage


class StatisticsService:
    def __init__(self, statistics_path: Path) -> None:
        ...

    def track_action(self, stage: AnnotationStage, message: str | None = None) -> float:
        ...

    def stop(self) -> None:
        ...
