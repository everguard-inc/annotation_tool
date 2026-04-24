from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QProgressBar, QVBoxLayout, QWidget


class ProgressDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(460, 130)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self._cancel_requested = False
        self._completed = False

        self.label = QLabel("Starting...", self)
        self.label.setWordWrap(True)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)

        self.setStyleSheet("""
            QDialog { background: #f5f5f5; color: #111; }
            QLabel { color: #111; font-size: 13px; }
            QProgressBar { color: #111; text-align: center; height: 22px; }
        """)

    def update_progress(
        self,
        percent: float,
        size_gb: float = 0.0,
        speed_mbps: float = 0.0,
        remaining_seconds: float = 0.0,
    ) -> None:
        percent = max(0.0, min(float(percent), 100.0))
        self.progress_bar.setValue(int(percent))

        if remaining_seconds > 0:
            self.label.setText(
                f"Progress: {percent:.1f}% | "
                f"Downloaded: {size_gb * 1024:.1f} MB | "
                f"Speed: {speed_mbps:.1f} MB/s | "
                f"Remaining: {int(remaining_seconds)} sec"
            )
        else:
            self.label.setText(f"Progress: {percent:.1f}%")

        QApplication.processEvents()

    def mark_complete(self) -> None:
        self._completed = True
        self.update_progress(100)
        self.close()
        QApplication.processEvents()

    def should_cancel(self) -> bool:
        return self._cancel_requested

    def closeEvent(self, event) -> None:
        if not self._completed:
            self._cancel_requested = True
        event.accept()
