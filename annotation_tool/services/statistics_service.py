import time
from pathlib import Path

from annotation_tool.core.enums import AnnotationStage
from annotation_tool.core.utils import now_string


class StatisticsService:
    def __init__(self, statistics_path: Path) -> None:
        self.statistics_path = statistics_path
        self.tick_time = time.time()
        self.duration_hours = 0.0
        self.max_action_time_sec = 60 * 5
        self.enabled = True

    def track_action(self, stage: AnnotationStage, message: str | None = None) -> float:
        if not self.enabled:
            return self.duration_hours

        current_time = time.time()
        interval = current_time - self.tick_time

        if interval <= 1:
            return self.duration_hours

        self.statistics_path.parent.mkdir(parents=True, exist_ok=True)
        with self.statistics_path.open("a", encoding="utf-8") as file:
            file.write(f"{stage.name},{now_string()},{message or ''}\n")

        self.tick_time = current_time
        self.duration_hours += min(interval, self.max_action_time_sec) / 3600
        return self.duration_hours

    def stop(self) -> None:
        self.enabled = False
