from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget


class BaseProjectScreen(QWidget, ABC):
    @abstractmethod
    def save(self) -> None:
        ...

    @abstractmethod
    def close_screen(self) -> None:
        ...

    @abstractmethod
    def go_to_id(self, item_id: int) -> None:
        ...
