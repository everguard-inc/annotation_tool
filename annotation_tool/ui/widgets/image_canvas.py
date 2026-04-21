from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import QWidget


class ImageCanvas(QWidget):
    mouse_pressed = Signal(int, int)
    mouse_moved = Signal(int, int)
    mouse_released = Signal(int, int)
    mouse_hovered = Signal(int, int)
    key_pressed = Signal(str)
    key_released = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self._image = QImage()
        self._pixmap = QPixmap()

        self.scale_factor = 1.0
        self.min_scale_factor = 0.5
        self.max_scale_factor = 10.0
        self.x0 = 0.0
        self.y0 = 0.0

        self._panning = False
        self._pan_start_mouse = QPoint()
        self._pan_start_x0 = 0.0
        self._pan_start_y0 = 0.0

    def set_image(self, image: QImage) -> None:
        self._image = image
        self._pixmap = QPixmap.fromImage(image)
        self._update_min_scale()
        self._clamp_view()
        self.update()
        self.repaint()

    def fit_image(self) -> None:
        if self._image.isNull() or self.width() <= 0 or self.height() <= 0:
            return

        self._update_min_scale()
        fit_scale = min(self.width() / self._image.width(), self.height() / self._image.height())
        self.scale_factor = max(fit_scale, self.min_scale_factor)
        self.x0 = 0.0
        self.y0 = 0.0
        self._clamp_view()
        self.update()

    def image_coordinates(self, point: QPoint) -> tuple[int, int]:
        if self._image.isNull():
            return 0, 0

        x = int(point.x() / max(self.scale_factor, 1e-7) + self.x0)
        y = int(point.y() / max(self.scale_factor, 1e-7) + self.y0)

        x = max(0, min(x, self._image.width() - 1))
        y = max(0, min(y, self._image.height() - 1))
        return x, y

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)

        if self._image.isNull():
            return

        visible_width = self.width() / max(self.scale_factor, 1e-7)
        visible_height = self.height() / max(self.scale_factor, 1e-7)

        source = QRectF(self.x0, self.y0, visible_width, visible_height)
        target = QRectF(
            0,
            0,
            min(self.width(), self._image.width() * self.scale_factor),
            min(self.height(), self._image.height() * self.scale_factor),
        )

        painter.drawPixmap(target, self._pixmap, source)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()

        if event.button() == Qt.MouseButton.RightButton:
            self._panning = True
            self._pan_start_mouse = event.pos()
            self._pan_start_x0 = self.x0
            self._pan_start_y0 = self.y0
            return

        if event.button() == Qt.MouseButton.LeftButton:
            x, y = self.image_coordinates(event.pos())
            self.mouse_pressed.emit(x, y)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._panning:
            dx = (self._pan_start_mouse.x() - event.pos().x()) / max(self.scale_factor, 1e-7)
            dy = (self._pan_start_mouse.y() - event.pos().y()) / max(self.scale_factor, 1e-7)
            self.x0 = self._pan_start_x0 + dx
            self.y0 = self._pan_start_y0 + dy
            self._clamp_view()
            self.update()

        x, y = self.image_coordinates(event.pos())
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.mouse_moved.emit(x, y)
        else:
            self.mouse_hovered.emit(x, y)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = False
            return

        if event.button() == Qt.MouseButton.LeftButton:
            x, y = self.image_coordinates(event.pos())
            self.mouse_released.emit(x, y)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._image.isNull():
            return

        cursor_x, cursor_y = self.image_coordinates(event.position().toPoint())

        multiplier = 1.1
        if event.angleDelta().y() > 0:
            self.scale_factor = min(self.scale_factor * multiplier, self.max_scale_factor)
        else:
            self.scale_factor = max(self.scale_factor / multiplier, self.min_scale_factor)

        self.x0 = cursor_x - event.position().x() / self.scale_factor
        self.y0 = cursor_y - event.position().y() / self.scale_factor

        self._clamp_view()
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return

        key = self._event_to_key(event)
        if key:
            self.key_pressed.emit(key)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return

        key = self._event_to_key(event)
        if key:
            self.key_released.emit(key)

    def resizeEvent(self, event) -> None:
        self._update_min_scale()
        self._clamp_view()
        self.update()

    def _event_to_key(self, event: QKeyEvent) -> str:
        modifiers = event.modifiers()
        key = event.key()

        if modifiers & Qt.KeyboardModifier.ControlModifier or modifiers & Qt.KeyboardModifier.MetaModifier:
            if key == Qt.Key.Key_Z:
                return "ctrl+z"
            if key == Qt.Key.Key_Y:
                return "ctrl+y"
            if key == Qt.Key.Key_C:
                return "ctrl+c"
            if key == Qt.Key.Key_V:
                return "ctrl+v"

        if key in {Qt.Key.Key_Shift}:
            return "shift"
        if key == Qt.Key.Key_Space:
            return "space"
        if key == Qt.Key.Key_Escape:
            return "escape"

        return event.text().lower() if event.text() else ""

    def _update_min_scale(self) -> None:
        if self._image.isNull() or self.width() <= 0 or self.height() <= 0:
            self.min_scale_factor = 0.5
            return

        fit_scale = min(self.width() / self._image.width(), self.height() / self._image.height())
        self.min_scale_factor = min(0.5, fit_scale)

    def _clamp_view(self) -> None:
        if self._image.isNull():
            self.x0 = 0.0
            self.y0 = 0.0
            return

        self.scale_factor = max(self.min_scale_factor, min(self.scale_factor, self.max_scale_factor))

        visible_width = self.width() / max(self.scale_factor, 1e-7)
        visible_height = self.height() / max(self.scale_factor, 1e-7)

        max_x0 = max(0.0, self._image.width() - visible_width)
        max_y0 = max(0.0, self._image.height() - visible_height)

        self.x0 = max(0.0, min(self.x0, max_x0))
        self.y0 = max(0.0, min(self.y0, max_y0))
