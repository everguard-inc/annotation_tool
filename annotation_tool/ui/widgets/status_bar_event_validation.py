from PySide6.QtGui import QFont, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from annotation_tool.services.event_validation_session import EventValidationStatusData


class EventValidationStatusBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.mode_label = QLabel("Mode: Event validation", self)
        self.item_id_label = QLabel(self)
        self.speed_label = QLabel(self)
        self.processed_label = QLabel(self)
        self.progress_bar = QProgressBar(self)
        self.duration_label = QLabel(self)
        self.preview_label = QLabel(self)
        self.frame_label = QLabel(self)

        self.progress_bar.setRange(0, 100)

        layout = QHBoxLayout(self)
        for widget in (
            self.mode_label,
            self.item_id_label,
            self.speed_label,
            self.processed_label,
            self.progress_bar,
            self.duration_label,
            self.preview_label,
            self.frame_label,
        ):
            layout.addWidget(widget)

    def update_status(self, status: EventValidationStatusData) -> None:
        percent = int((status.item_id + 1) / max(status.items_count, 1) * 100)

        self.item_id_label.setText(f"Event id: {status.item_id}")
        self.speed_label.setText(f"Speed: {status.speed_per_hour} event/hour")
        self.processed_label.setText(
            f"Position: {percent} % ({status.item_id + 1}/{status.items_count})"
        )
        self.progress_bar.setValue(percent)
        self.duration_label.setText(f"Duration: {status.duration_hours:.2f} hours")
        self.preview_label.setText(f"Preview: {status.view_mode}")
        self.frame_label.setText(
            f"Frame: {status.current_frame_number}/{status.number_of_frames}"
        )

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        size = max(8, min(15, int(self.width() / 130)))
        for label in (
            self.mode_label,
            self.item_id_label,
            self.speed_label,
            self.processed_label,
            self.duration_label,
            self.preview_label,
            self.frame_label,
        ):
            font = QFont(label.font())
            font.setPointSize(size)
            label.setFont(font)
