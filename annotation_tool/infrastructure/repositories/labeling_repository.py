from annotation_tool.core.models import LabelData


class LabelingRepository:
    def get_labels(self) -> list[LabelData]:
        ...

    def get_figure_labels(self) -> list[LabelData]:
        ...

    def get_review_labels(self) -> list[LabelData]:
        ...

    def save_labels(self, labels: list[LabelData]) -> None:
        ...

    def list_image_names(self) -> list[str]:
        ...

    def load_image_annotations(self, image_name: str) -> object:
        ...

    def save_image_annotations(self, image_name: str, annotations: object) -> None:
        ...

    def count_review_labels(self) -> int:
        ...
