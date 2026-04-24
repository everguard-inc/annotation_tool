from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QImage, QWheelEvent

from annotation_tool.ui.widgets.image_canvas import ImageCanvas


def test_canvas_fits_image_and_clamps_coordinates(qapp) -> None:
    """Covers FR-122, FR-123, FR-124, FR-125, FR-126, FR-127."""
    canvas = ImageCanvas()
    canvas.resize(200, 100)
    canvas.set_image(QImage(100, 50, QImage.Format.Format_RGB888))

    canvas.fit_image()

    assert canvas.scale_factor == 2.0
    assert canvas.image_coordinates(QPoint(0, 0)) == (0, 0)
    assert canvas.image_coordinates(QPoint(199, 99)) == (99, 49)

    canvas.x0 = 10_000
    canvas.y0 = 10_000
    canvas._clamp_view()

    assert canvas.x0 == 0
    assert canvas.y0 == 0


def test_canvas_refits_image_when_viewport_shrinks(qapp) -> None:
    """Regression: first-show / resize should keep the image fitted instead
    of preserving an older, larger zoom that crops the image."""
    canvas = ImageCanvas()
    canvas.resize(1000, 800)
    canvas.set_image(QImage(1920, 1080, QImage.Format.Format_RGB888))

    canvas.fit_image()
    assert canvas.scale_factor == 1000 / 1920

    canvas.show()
    qapp.processEvents()
    canvas.resize(778, 691)
    qapp.processEvents()

    assert canvas.scale_factor == min(778 / 1920, 691 / 1080)


def test_canvas_centers_fitted_image_and_maps_coordinates_from_centered_view(
    qapp,
) -> None:
    canvas = ImageCanvas()
    canvas.resize(2048, 1070)
    canvas.set_image(QImage(1920, 1080, QImage.Format.Format_RGB888))
    canvas.fit_image()

    target = canvas._target_rect()
    assert target.x() > 0
    assert target.width() == 1920 * canvas.scale_factor

    left_edge = QPoint(int(target.x()), int(target.y()))
    right_edge = QPoint(
        int(target.x() + target.width() + 50), int(target.y() + target.height() + 50)
    )

    assert canvas.image_coordinates(left_edge) == (0, 0)
    assert canvas.image_coordinates(right_edge) == (1919, 1079)


def test_canvas_renders_image_at_same_scale_as_coordinate_mapping(qapp) -> None:
    """Regression: when the widget aspect ratio differs from the image, the
    paint-event source/target must be proportional by scale_factor — otherwise
    annotations drawn in image-pixel space (crosshair, bboxes) land at widget
    positions that disagree with where the user actually clicked."""
    canvas = ImageCanvas()
    canvas.resize(2048, 1070)

    image = QImage(1920, 1080, QImage.Format.Format_RGB888)
    image.fill(0xFF000000)
    marker_image_x = 1500
    marker_image_y = 540
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            image.setPixel(marker_image_x + dx, marker_image_y + dy, 0xFFFF0000)

    canvas.set_image(image)
    canvas.fit_image()
    canvas.show()
    qapp.processEvents()

    rendered = canvas.grab().toImage()

    target = canvas._target_rect()
    expected_widget_x = int(
        target.x() + marker_image_x * target.width() / image.width()
    )
    expected_widget_y = int(
        target.y() + marker_image_y * target.height() / image.height()
    )

    pixel = rendered.pixelColor(expected_widget_x, expected_widget_y)
    assert (pixel.red(), pixel.green(), pixel.blue()) == (255, 0, 0)


def test_canvas_wheel_zoom_keeps_cursor_image_coordinate_stable_when_letterboxed(
    qapp,
    monkeypatch,
) -> None:
    canvas = ImageCanvas()
    canvas.resize(400, 400)
    canvas.set_image(QImage(100, 200, QImage.Format.Format_RGB888))
    canvas.fit_image()

    target = canvas._target_rect()
    assert target.x() > 0
    cursor = QPoint(int(target.x() + target.width() * 0.75), int(target.y() + 100))
    before = canvas.image_coordinates(cursor)
    monkeypatch.setattr(canvas, "_clamp_view", lambda: None)
    event = QWheelEvent(
        QPointF(cursor),
        QPointF(cursor),
        QPoint(0, 120),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )

    canvas.wheelEvent(event)

    assert canvas.image_coordinates(cursor) == before
