from abc import ABC, abstractmethod

from PySide6.QtWidgets import QWidget


class BaseProjectScreen(QWidget):
    @property
    @abstractmethod
    def items_count(self) -> int:
        ...

    @property
    @abstractmethod
    def duration_hours(self) -> float:
        ...

    @abstractmethod
    def save(self) -> None:
        ...

    @abstractmethod
    def close_screen(self) -> None:
        ...

    @abstractmethod
    def go_to_id(self, item_id: int) -> None:
        ...

    def export_results(self) -> list:
        return []

    def should_remove_after_completion(self) -> bool:
        return False
