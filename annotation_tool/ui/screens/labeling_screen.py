from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.ui.screens.base_screen import BaseProjectScreen


class LabelingScreen(BaseProjectScreen):
    def __init__(self, session: LabelingSession, parent=None) -> None:
        ...

    def refresh(self) -> None:
        ...

    def save(self) -> None:
        ...

    def close_screen(self) -> None:
        ...

    def go_to_id(self, item_id: int) -> None:
        ...

    def show_classes(self) -> None:
        ...

    def show_review_labels(self) -> None:
        ...

    def overwrite_annotations(self) -> None:
        ...
