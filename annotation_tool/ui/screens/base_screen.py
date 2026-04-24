from PySide6.QtWidgets import QWidget


class BaseProjectScreen(QWidget):
    @property
    def items_count(self) -> int:
        raise NotImplementedError

    @property
    def duration_hours(self) -> float:
        raise NotImplementedError

    def save(self) -> None:
        raise NotImplementedError

    def close_screen(self) -> None:
        raise NotImplementedError

    def go_to_id(self, item_id: int) -> None:
        raise NotImplementedError

    def reload_current_annotations(self) -> None:
        """Re-read the current item from the repository without persisting
        any in-memory edits first. Used after a download-and-overwrite so
        the fresh annotations are not clobbered by a stale save."""
        raise NotImplementedError

    def export_results(self) -> list:
        return []

    def should_remove_after_completion(self) -> bool:
        return False
