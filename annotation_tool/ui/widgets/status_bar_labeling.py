from PySide6.QtWidgets import QLabel, QProgressBar, QWidget, QHBoxLayout

from annotation_tool.core.models import LabelingStatusData


class LabelingStatusBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.mode_label = QLabel(self)
        self.class_label = QLabel(self)
        self.trash_label = QLabel(self)
        self.hidden_label = QLabel(self)
        self.item_id_label = QLabel(self)
        self.speed_label = QLabel(self)
        self.processed_label = QLabel(self)
        self.progress_bar = QProgressBar(self)
        self.duration_label = QLabel(self)

        self.progress_bar.setRange(0, 100)

        layout = QHBoxLayout(self)
        for widget in (
            self.mode_label,
            self.class_label,
            self.trash_label,
            self.hidden_label,
            self.item_id_label,
            self.speed_label,
            self.processed_label,
            self.progress_bar,
            self.duration_label,
        ):
            layout.addWidget(widget)

    def update_status(self, status: LabelingStatusData) -> None:
        percent = int((status.item_id + 1) / max(status.items_count, 1) * 100)

        self.mode_label.setText(f"Mode: {status.annotation_mode}: {status.annotation_stage}")
        self.class_label.setText(f"Class: {status.selected_class}")
        self.trash_label.setText("Trash" if status.is_trash else "not Trash")

        if status.figures_hidden:
            hidden_text = "All Hidden"
        elif status.review_labels_hidden:
            hidden_text = "Review Hidden"
        else:
            hidden_text = "All Visible"

        self.hidden_label.setText(hidden_text)
        self.item_id_label.setText(f"Img id: {status.item_id}")
        self.speed_label.setText(f"Speed: {status.speed_per_hour} img/hour")
        self.processed_label.setText(f"Position: {percent} % ({status.item_id + 1}/{status.items_count})")
        self.progress_bar.setValue(percent)
        self.duration_label.setText(f"Duration: {status.duration_hours:.2f} hours")
