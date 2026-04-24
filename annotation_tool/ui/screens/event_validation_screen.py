from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from annotation_tool.core.utils import write_json
from annotation_tool.media.image_converter import numpy_to_qimage
from annotation_tool.services.event_validation_session import EventValidationSession
from annotation_tool.ui.screens.base_screen import BaseProjectScreen
from annotation_tool.ui.widgets.image_canvas import ImageCanvas
from annotation_tool.ui.widgets.status_bar_event_validation import (
    EventValidationStatusBar,
)


class EventValidationScreen(BaseProjectScreen):
    def __init__(
        self, session: EventValidationSession, results_path: Path, parent=None
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.results_path = results_path
        self.held_navigation_key: str | None = None
        self.navigation_in_progress = False
        self.syncing_slider = False

        self.canvas = ImageCanvas(self)
        self.status_bar = EventValidationStatusBar(self)
        self.sidebar = QWidget(self)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.play_button = QPushButton("Play", self)
        self.stop_button = QPushButton("Stop", self)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.canvas, stretch=1)
        content_layout.addWidget(self.sidebar)

        playback_layout = QHBoxLayout()
        playback_layout.addWidget(self.slider, stretch=1)
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.stop_button)

        layout = QVBoxLayout(self)
        layout.addLayout(content_layout, stretch=1)
        layout.addLayout(playback_layout)
        layout.addWidget(self.status_bar)

        self.canvas.key_pressed.connect(self.handle_key_press)
        self.canvas.key_released.connect(self.handle_key_release)
        self.slider.valueChanged.connect(self._handle_slider_change)
        self.play_button.clicked.connect(self._toggle_playback)
        self.stop_button.clicked.connect(self._stop_playback)

        self.navigation_timer = QTimer(self)
        self.navigation_timer.timeout.connect(self._repeat_navigation)
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self._play_next_frame)

        self.refresh(fit=True)

    @property
    def items_count(self) -> int:
        return self.session.item_count()

    @property
    def duration_hours(self) -> float:
        return self.session.duration_hours

    def refresh(self, fit: bool = False) -> None:
        self._build_sidebar()
        self.canvas.set_image(numpy_to_qimage(self.session.current_frame()))

        if fit:
            self.canvas.fit_image()

        status = self.session.status()
        self._update_playback_controls(status)
        self.status_bar.update_status(status)

    def save(self) -> None:
        self.session.save_current_item()

    def close_screen(self) -> None:
        self.navigation_timer.stop()
        self.playback_timer.stop()
        self.held_navigation_key = None
        self.session.close()

    def go_to_id(self, item_id: int) -> None:
        self.session.go_to_item(item_id)
        self.refresh(fit=True)

    def reload_current_annotations(self) -> None:
        self.session.load_current_item()
        self.refresh(fit=True)

    def export_results(self) -> list[Path]:
        self.session.save_current_item()
        write_json(
            self.results_path,
            {
                "fields": list(self.session.fields.keys()),
                "events": {
                    event["uid"]: {
                        "answers": event.get("answers", []),
                        "comment": event.get("comment") or "",
                    }
                    for event in self.session.repository.events()
                },
            },
        )
        return [self.results_path]

    def should_remove_after_completion(self) -> bool:
        return False

    def handle_key_press(self, key: str) -> None:
        if key in {"w", "p", "q", "o"}:
            self.held_navigation_key = key
            if not self.navigation_timer.isActive():
                self._repeat_navigation()
                self.navigation_timer.start(100)
            return

        if key == "f":
            self.canvas.fit_image()
            return

        if key == "x":
            self.session.video_forward()
        elif key == "z":
            self.session.video_backward()
        elif key == "a":
            self.session.set_image_mode()
        elif key == "s":
            self.session.set_video_mode()
        elif key.isdigit() and key != "0":
            question_index = int(key) - 1
            if question_index < len(self.session.questions):
                self.session.cycle_answer(self.session.questions[question_index])

        self.refresh()

    def handle_key_release(self, key: str) -> None:
        if key == self.held_navigation_key:
            self.held_navigation_key = None
            self.navigation_timer.stop()

    def _repeat_navigation(self) -> None:
        if self.navigation_in_progress or self.held_navigation_key is None:
            return

        self.navigation_in_progress = True
        try:
            if self.held_navigation_key in {"w", "p"}:
                self.session.next_item()
            elif self.held_navigation_key in {"q", "o"}:
                self.session.previous_item()
            self.refresh(fit=True)
        finally:
            self.navigation_in_progress = False

    def _handle_slider_change(self, value: int) -> None:
        if self.syncing_slider:
            return

        self.session.load_video_frame(value - 1)
        self.refresh()

    def _toggle_playback(self) -> None:
        if self.playback_timer.isActive():
            self._pause_playback()
            return

        self.play_button.setText("Pause")
        self.playback_timer.start(10)

    def _pause_playback(self) -> None:
        self.playback_timer.stop()
        self.play_button.setText("Play")

    def _stop_playback(self) -> None:
        self._pause_playback()
        self.session.load_video_frame(0)
        self.refresh()

    def _play_next_frame(self) -> None:
        status = self.session.status()
        if status.current_frame_number >= status.number_of_frames:
            self._pause_playback()
            return

        self.session.video_forward()
        self.refresh()

    def _update_playback_controls(self, status) -> None:
        video_mode = status.view_mode == "VIDEO"
        for widget in (self.slider, self.play_button, self.stop_button):
            widget.setVisible(video_mode)

        if not video_mode:
            self._pause_playback()
            return

        self.syncing_slider = True
        try:
            self.slider.setRange(1, max(status.number_of_frames, 1))
            self.slider.setValue(
                max(1, min(status.current_frame_number, max(status.number_of_frames, 1)))
            )
        finally:
            self.syncing_slider = False

    def _build_sidebar(self) -> None:
        self._clear_sidebar()

        for index, question in enumerate(self.session.questions, start=1):
            self.sidebar_layout.addWidget(QLabel(f"{index}. {question}", self.sidebar))
            combo = QComboBox(self.sidebar)
            combo.addItems(["", *list(self.session.fields[question].keys())])
            current_answer = self.session.answers.get(question, "")
            combo.setCurrentText(current_answer)
            combo.currentTextChanged.connect(
                lambda answer, selected_question=question: self.session.update_answer(
                    selected_question, answer
                )
            )
            self.sidebar_layout.addWidget(combo)

        self.sidebar_layout.addWidget(QLabel("Comment", self.sidebar))
        comment = QTextEdit(self.sidebar)
        comment.setPlainText(self.session.comment)
        comment.textChanged.connect(
            lambda editor=comment: self.session.update_comment(editor.toPlainText())
        )
        self.sidebar_layout.addWidget(comment)
        self.sidebar_layout.addStretch(1)

    def _clear_sidebar(self) -> None:
        while self.sidebar_layout.count():
            item = self.sidebar_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
