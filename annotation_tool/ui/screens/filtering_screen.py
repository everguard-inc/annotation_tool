from annotation_tool.services.filtering_session import FilteringSession
from annotation_tool.ui.screens.base_screen import BaseProjectScreen


class FilteringScreen(BaseProjectScreen):
    def __init__(self, session: FilteringSession, parent=None) -> None:
        ...

    def refresh(self) -> None:
        ...

    def save(self) -> None:
        ...

    def close_screen(self) -> None:
        ...

    def go_to_id(self, item_id: int) -> None:
        ...

    def toggle_selected(self) -> None:
        ...
