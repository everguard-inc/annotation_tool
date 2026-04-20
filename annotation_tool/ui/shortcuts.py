from PySide6.QtWidgets import QWidget


class ShortcutBinder:
    def __init__(self, target: QWidget) -> None:
        ...

    def bind_labeling_shortcuts(self) -> None:
        ...

    def bind_filtering_shortcuts(self) -> None:
        ...

    def clear(self) -> None:
        ...
