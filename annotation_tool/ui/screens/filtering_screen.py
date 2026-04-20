import time
from pathlib import Path

from PySide6.QtWidgets import QVBoxLayout

from annotation_tool.core.enums import FilteringDelay
from annotation_tool.media.image_converter import numpy_to_qimage
from annotation_tool.services.filtering_session import FilteringSession
from annotation_tool.ui.screens.base_screen import BaseProjectScreen
from annotation_tool.ui.widgets.image_canvas import ImageCanvas
from annotation_tool.ui.widgets.status_bar_filtering import FilteringStatusBar


class FilteringScreen(BaseProjectScreen):
    def __init__(self, session: FilteringSession, selected_frames_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.selected_frames_path = selected_frames_path
        self.last_frame_switch_time = 0.0

        self.canvas = ImageCanvas(self)
        self.status_bar = FilteringStatusBar(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.status_bar)

        self.canvas.key_pressed.connect(self.handle_key_press)
        self.canvas.mouse_hovered.connect(lambda *_: None)
        self.canvas.mouse_pressed.connect(lambda *_: None)
        self.canvas.mouse_moved.connect(lambda *_: None)
        self.canvas.mouse_released.connect(lambda *_: None)

        self.refresh(fit=True)

    @property
    def items_count(self) -> int:
        return self.session.item_count()

    @property
    def duration_hours(self) -> float:
        return self.session.duration_hours

    def refresh(self, fit: bool = False) -> None:
        self.canvas.set_image(numpy_to_qimage(self.session.current_frame()))

        if fit:
            self.canvas.fit_image()

        self.status_bar.update_status(self.session.status())

    def save(self) -> None:
        self.session.save_current_item()

    def close_screen(self) -> None:
        self.session.close()

    def go_to_id(self, item_id: int) -> None:
        self.session.go_to_item(item_id)
        self.refresh(fit=True)

    def toggle_selected(self) -> None:
        self.session.toggle_selected()
        self.refresh()

    def export_results(self) -> list:
        return [self.selected_frames_path]

    def should_remove_after_completion(self) -> bool:
        return False

    def handle_key_press(self, key: str) -> None:
        now = time.time()
        if now - self.last_frame_switch_time < self.session.delay.value:
            return

        if key in {"w", "p"}:
            self.session.next_item()
            self.last_frame_switch_time = now
            self.refresh(fit=True)
            return

        if key in {"q", "o"}:
            self.session.previous_item()
            self.last_frame_switch_time = now
            self.refresh(fit=True)
            return

        if key == "f":
            self.canvas.fit_image()
            return

        if key in {"d", "k"}:
            self.session.toggle_selected()
        elif key == "z":
            self.session.go_to_previous_selected()
        elif key == "x":
            self.session.go_to_next_selected()
        elif key == "s":
            self.session.toggle_degraded_preview()
        elif key == "1":
            self.session.set_delay(FilteringDelay.NO_DELAY)
        elif key == "2":
            self.session.set_delay(FilteringDelay.SHORT)
        elif key == "3":
            self.session.set_delay(FilteringDelay.MIDDLE)
        elif key == "4":
            self.session.set_delay(FilteringDelay.LONG)

        self.refresh()
