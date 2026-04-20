from annotation_tool.ui.screens.base_screen import BaseProjectScreen


class EventValidationScreen(BaseProjectScreen):
    def save(self) -> None:
        ...

    def close_screen(self) -> None:
        ...

    def go_to_id(self, item_id: int) -> None:
        ...
