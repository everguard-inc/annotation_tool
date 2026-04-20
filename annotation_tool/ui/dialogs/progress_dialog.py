from PySide6.QtWidgets import QDialog


class ProgressDialog(QDialog):
    def __init__(self, title: str, parent=None) -> None:
        ...

    def update_progress(
        self,
        percent: float,
        completed_gb: float,
        speed_mbps: float,
        remaining_seconds: float,
    ) -> None:
        ...

    def mark_complete(self) -> None:
        ...

    def was_cancelled(self) -> bool:
        ...
