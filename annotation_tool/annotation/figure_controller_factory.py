from annotation_tool.core.enums import AnnotationMode
from annotation_tool.annotation.figure_controller import FigureController


class FigureControllerFactory:
    def create(self, mode: AnnotationMode, active_label: str) -> FigureController:
        ...
