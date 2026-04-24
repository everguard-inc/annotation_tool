from annotation_tool.annotation.figure_controller import FigureController
from annotation_tool.annotation.figures import AnnotationStyle
from annotation_tool.core.enums import AnnotationMode
from annotation_tool.core.models import LabelData


class FigureControllerFactory:
    def create(
        self,
        mode: AnnotationMode,
        active_label: LabelData | None,
        annotation_style: AnnotationStyle | None = None,
    ) -> FigureController:
        return FigureController(
            mode=mode,
            active_label=active_label,
            annotation_style=annotation_style,
        )
