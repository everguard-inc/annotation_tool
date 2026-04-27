from PySide6.QtGui import QFont, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from annotation_tool.core.models import FilteringStatusData


class FilteringStatusBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.mode_label = QLabel("Mode: Filtering", self)
        self.delay_label = QLabel(self)
        self.selected_label = QLabel(self)
        self.item_id_label = QLabel(self)
        self.speed_label = QLabel(self)
        self.selected_ratio_label = QLabel(self)
        self.processed_label = QLabel(self)
        self.progress_bar = QProgressBar(self)
        self.duration_label = QLabel(self)

        self.progress_bar.setRange(0, 100)

        layout = QHBoxLayout(self)
        for widget in (
            self.mode_label,
            self.delay_label,
            self.selected_label,
            self.item_id_label,
            self.speed_label,
            self.selected_ratio_label,
            self.processed_label,
            self.progress_bar,
            self.duration_label,
        ):
            layout.addWidget(widget)

    def update_status(self, status: FilteringStatusData) -> None:
        percent = int((status.item_id + 1) / max(status.items_count, 1) * 100)
        selected_ratio = status.selected_count / max(status.processed_count, 1) * 100

        self.delay_label.setText(f"Delay: {status.delay}")
        self.selected_label.setText(
            "Selected: TRUE" if status.selected else "Selected: FALSE"
        )
        self.item_id_label.setText(f"Img id: {status.item_id}")
        self.speed_label.setText(f"Speed: {status.speed_per_hour} img/hour")
        self.selected_ratio_label.setText(
            f"Selected: {selected_ratio:.2f}% ({status.selected_count} selected / {status.processed_count} viewed)"
        )
        self.processed_label.setText(
            f"Position: {percent} % ({status.item_id + 1}/{status.items_count})"
        )
        self.progress_bar.setValue(percent)
        self.duration_label.setText(f"Duration: {status.duration_hours:.2f} hours")

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        size = max(8, min(15, int(self.width() / 130)))
        for label in (
            self.mode_label,
            self.delay_label,
            self.selected_label,
            self.item_id_label,
            self.speed_label,
            self.selected_ratio_label,
            self.processed_label,
            self.duration_label,
        ):
            font = QFont(label.font())
            font.setPointSize(size)
            label.setFont(font)
