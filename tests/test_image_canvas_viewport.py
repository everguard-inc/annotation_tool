from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage

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
