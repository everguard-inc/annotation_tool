from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout

from annotation_tool.core.enums import FilteringDelay
from annotation_tool.core.utils import write_json
from annotation_tool.media.image_converter import numpy_to_qimage
from annotation_tool.services.filtering_session import FilteringSession
from annotation_tool.ui.screens.base_screen import BaseProjectScreen
from annotation_tool.ui.widgets.image_canvas import ImageCanvas
from annotation_tool.ui.widgets.status_bar_filtering import FilteringStatusBar


class FilteringScreen(BaseProjectScreen):
    def __init__(
        self, session: FilteringSession, selected_frames_path: Path, parent=None
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.selected_frames_path = selected_frames_path
        self.held_navigation_key: str | None = None
        self.navigation_in_progress = False

        self.canvas = ImageCanvas(self)
        self.status_bar = FilteringStatusBar(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.status_bar)

        self.canvas.key_pressed.connect(self.handle_key_press)
        self.canvas.key_released.connect(self.handle_key_release)

        self.navigation_timer = QTimer(self)
        self.navigation_timer.timeout.connect(self._repeat_navigation)

        QTimer.singleShot(0, lambda: self.refresh(fit=True))

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
        self.navigation_timer.stop()
        self.held_navigation_key = None
        self.session.close()

    def go_to_id(self, item_id: int) -> None:
        self.session.go_to_item(item_id)
        self.refresh(fit=True)

    def reload_current_annotations(self) -> None:
        self.session.load_current_item()
        self.refresh(fit=True)

    def toggle_selected(self) -> None:
        self.session.toggle_selected()
        self.refresh()

    def export_results(self) -> list:
        self.session.save_current_item()
        if hasattr(self.session.repository, "flush"):
            self.session.repository.flush()
        result = {"names": [], "ids": []}
        for item in self.session.repository.list_items():
            if not item.get("selected"):
                continue
            if item.get("name"):
                result["names"].append(item["name"])
            elif item.get("item_id") is not None:
                result["ids"].append(item["item_id"])
        write_json(self.selected_frames_path, result)
        return [self.selected_frames_path]

    def should_remove_after_completion(self) -> bool:
        return True

    def handle_key_press(self, key: str) -> None:
        if key in {"w", "p", "q", "o"}:
            self.held_navigation_key = key

            if not self.navigation_timer.isActive():
                self._repeat_navigation()
                self.navigation_timer.start(self._navigation_interval_ms())
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
            self._restart_timer_if_needed()
        elif key == "2":
            self.session.set_delay(FilteringDelay.SHORT)
            self._restart_timer_if_needed()
        elif key == "3":
            self.session.set_delay(FilteringDelay.MIDDLE)
            self._restart_timer_if_needed()
        elif key == "4":
            self.session.set_delay(FilteringDelay.LONG)
            self._restart_timer_if_needed()

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

    def _navigation_interval_ms(self) -> int:
        return max(1, int(self.session.delay.value * 1000))

    def _restart_timer_if_needed(self) -> None:
        if self.navigation_timer.isActive():
            self.navigation_timer.start(self._navigation_interval_ms())
