from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout


class ProgressDialog(QDialog):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(460, 140)

        self._cancelled = False

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)

        self.percent_label = QLabel("Starting...", self)
        self.size_label = QLabel("Completed: 0 MB", self)
        self.speed_label = QLabel("Speed: 0 MB/s", self)
        self.remaining_label = QLabel("Remaining: --:--:--", self)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self._cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.progress)
        layout.addWidget(self.percent_label)
        layout.addWidget(self.size_label)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.remaining_label)
        layout.addWidget(self.cancel_button)

    def update_progress(
        self,
        percent: float,
        completed_gb: float,
        speed_mbps: float,
        remaining_seconds: float,
    ) -> None:
        self.progress.setValue(int(percent))
        self.percent_label.setText(f"Completed: {percent:.2f} %")

        if completed_gb < 1:
            self.size_label.setText(f"Completed: {completed_gb * 1024:.2f} MB")
        else:
            self.size_label.setText(f"Completed: {completed_gb:.2f} GB")

        self.speed_label.setText(f"Speed: {speed_mbps:.2f} MB/s")

        hours = int(remaining_seconds) // 3600
        minutes = int(remaining_seconds) % 3600 // 60
        seconds = int(remaining_seconds) % 60
        self.remaining_label.setText(f"Remaining: {hours:02}:{minutes:02}:{seconds:02}")

    def mark_complete(self) -> None:
        self.progress.setValue(100)
        self.percent_label.setText("Completed: 100.00 %")
        self.cancel_button.setText("Close")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.accept)

    def was_cancelled(self) -> bool:
        return self._cancelled

    def _cancel(self) -> None:
        self._cancelled = True
        self.reject()
