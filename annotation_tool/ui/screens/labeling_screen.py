import time

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QVBoxLayout

from annotation_tool.media.image_converter import numpy_to_qimage
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.ui.screens.base_screen import BaseProjectScreen
from annotation_tool.ui.widgets.class_wheel_overlay import ClassWheelOverlay
from annotation_tool.ui.widgets.image_canvas import ImageCanvas
from annotation_tool.ui.widgets.status_bar_labeling import LabelingStatusBar


class LabelingScreen(BaseProjectScreen):
    def __init__(self, session: LabelingSession, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.last_frame_switch_time = 0.0
        self.min_frame_switch_interval = 0.1

        self.canvas = ImageCanvas(self)
        self.status_bar = LabelingStatusBar(self)
        self.class_wheel = ClassWheelOverlay(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.status_bar)

        self.canvas.mouse_pressed.connect(self.handle_mouse_press)
        self.canvas.mouse_moved.connect(self.handle_mouse_move)
        self.canvas.mouse_released.connect(self.handle_mouse_release)
        self.canvas.mouse_hovered.connect(self.handle_mouse_hover)
        self.canvas.key_pressed.connect(self.handle_key_press)
        self.canvas.key_released.connect(self.handle_key_release)

        self.refresh(fit=True)

    @property
    def items_count(self) -> int:
        return self.session.item_count()

    @property
    def duration_hours(self) -> float:
        return self.session.duration_hours

    def refresh(self, fit: bool = False) -> None:
        self.canvas.set_image(numpy_to_qimage(self.session.render_frame()))
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

    def show_classes(self) -> None:
        pass

    def show_review_labels(self) -> None:
        pass

    def overwrite_annotations(self) -> None:
        pass

    def export_results(self) -> list:
        return []

    def should_remove_after_completion(self) -> bool:
        return False

    def handle_mouse_press(self, x: int, y: int) -> None:
        self.session.set_cursor(x, y)
        self.session.handle_mouse_press(x, y)
        self.refresh()

    def handle_mouse_move(self, x: int, y: int) -> None:
        self.session.set_cursor(x, y)
        self.session.handle_mouse_move(x, y)
        self.refresh()

    def handle_mouse_release(self, x: int, y: int) -> None:
        self.session.set_cursor(x, y)
        self.session.handle_mouse_release(x, y)
        self.refresh()

    def handle_mouse_hover(self, x: int, y: int) -> None:
        self.session.set_cursor(x, y)
        self.session.handle_mouse_hover(x, y)
        self.refresh()

    def handle_key_press(self, key: str) -> None:
        now = time.time()

        if key in {"w", "p"}:
            if now - self.last_frame_switch_time >= self.min_frame_switch_interval:
                self.session.next_item()
                self.last_frame_switch_time = now
                self.refresh(fit=True)
            return

        if key in {"q", "o"}:
            if now - self.last_frame_switch_time >= self.min_frame_switch_interval:
                self.session.previous_item()
                self.last_frame_switch_time = now
                self.refresh(fit=True)
            return

        if key == "f":
            self.canvas.fit_image()
            return

        if key == "shift":
            self.session.set_shift_mode(True)
            return

        if key == "space":
            self.session.finish_polygon()
        elif key == "escape":
            self.session.cancel_polygon()
        elif key == "a":
            self.class_wheel.open_at(QPoint(self.session.cursor_x, self.session.cursor_y), self.session.labels())
            return
        elif key == "d":
            self.session.delete_selected()
        elif key == "g":
            self.session.delete_all()
        elif key == "t":
            self.session.toggle_trash()
        elif key == "e":
            self.session.toggle_figures_visibility()
        elif key == "r":
            self.session.toggle_review_labels_visibility()
        elif key == "n":
            self.session.toggle_label_names()
        elif key == "h":
            self.session.toggle_object_size()
        elif key == "s":
            self.session.toggle_degraded_preview()
        elif key == "u":
            self.session.copy_from_previous_item()
        elif key == "ctrl+z":
            self.session.undo()
        elif key == "ctrl+y":
            self.session.redo()
        elif key == "ctrl+c":
            self.session.copy()
        elif key == "ctrl+v":
            self.session.paste()
        elif key.isdigit():
            self.session.set_active_label_by_hotkey(key)

        self.refresh()

    def handle_key_release(self, key: str) -> None:
        if key == "shift":
            self.session.set_shift_mode(False)
            return

        if key == "a":
            selected = self.class_wheel.selected_label(QPoint(self.session.cursor_x, self.session.cursor_y))
            if selected is not None:
                self.session.set_active_label_by_hotkey(selected.hotkey)
            self.class_wheel.close()
            self.refresh()
