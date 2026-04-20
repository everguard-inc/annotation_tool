from PySide6.QtCore import QPoint

from annotation_tool.core.enums import FigureType
from annotation_tool.core.models import LabelData
from annotation_tool.ui.widgets.class_wheel_overlay import ClassWheelOverlay


def test_class_wheel_selects_label_by_cursor_direction(qapp) -> None:
    """Covers FR-139, FR-140, FR-141, FR-142."""
    wheel = ClassWheelOverlay()
    labels = [
        LabelData(name="car", color="red", hotkey="1", type=FigureType.BBOX),
        LabelData(name="truck", color="blue", hotkey="2", type=FigureType.BBOX),
        LabelData(name="bus", color="green", hotkey="3", type=FigureType.BBOX),
        LabelData(name="person", color="yellow", hotkey="4", type=FigureType.BBOX),
    ]

    wheel.open_at(QPoint(10, 10), labels)

    assert wheel.selected_label(QPoint(20, 10)).name == "car"
    assert wheel.selected_label(QPoint(10, 20)).name == "truck"
    assert wheel.selected_label(QPoint(0, 10)).name == "bus"
