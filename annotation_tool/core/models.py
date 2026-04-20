from dataclasses import dataclass
from typing import Any

from annotation_tool.core.enums import AnnotationMode, AnnotationStage, FigureType


@dataclass
class ProjectData:
    id: int
    uid: str | None
    stage: AnnotationStage
    mode: AnnotationMode

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectData":
        ...

    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass
class CheckResult:
    ready_to_complete: bool
    message: str = ""


@dataclass
class LabelData:
    name: str
    color: str
    hotkey: str
    type: FigureType
    attributes: dict[str, Any] | None = None


@dataclass
class StatusData:
    item_id: int
    items_count: int
    duration_hours: float
    speed_per_hour: float
    processed_count: int


@dataclass
class LabelingStatusData(StatusData):
    selected_class: str
    class_color: str
    is_trash: bool
    annotation_mode: str
    annotation_stage: str
    figures_hidden: bool
    review_labels_hidden: bool


@dataclass
class FilteringStatusData(StatusData):
    delay: str
    selected: bool
    selected_count: int
