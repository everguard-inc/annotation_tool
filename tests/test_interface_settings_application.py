import numpy as np

from annotation_tool.annotation.bboxes import BBox
from annotation_tool.annotation.figure_controller import FigureController
from annotation_tool.annotation.figures import AnnotationStyle, Point
from annotation_tool.annotation.keypoints import KeypointGroup
from annotation_tool.annotation.segmentation import Mask
from annotation_tool.core.enums import AnnotationMode


def test_bbox_draw_uses_configured_line_width_handler_size_and_fill_opacity(
    monkeypatch,
) -> None:
    rectangles = []
    circles = []

    def fake_rectangle(frame, p1, p2, color, thickness):
        rectangles.append(thickness)
        return frame

    def fake_circle(frame, center, radius, color, thickness):
        circles.append(radius)
        return frame

    monkeypatch.setattr("annotation_tool.annotation.bboxes.cv2.rectangle", fake_rectangle)
    monkeypatch.setattr("annotation_tool.annotation.bboxes.cv2.circle", fake_circle)

    style = AnnotationStyle(
        bbox_line_width=7,
        cursor_proximity_threshold=3,
        objects_opacity=0.9,
        color_fill_opacity=0.25,
        bbox_handler_size=9,
        keypoint_handler_size=5,
    )
    bbox = BBox(10, 10, 20, 20, "car")
    bbox.selected = True

    bbox.draw(np.zeros((30, 30, 3), dtype=np.uint8), 1.0, {"car": (0, 0, 255)}, style)

    assert rectangles[0] == -1
    assert rectangles[1] == 8
    assert all(radius == 9 for radius in circles)


def test_controller_uses_configured_cursor_proximity_for_selection() -> None:
    style = AnnotationStyle(
        bbox_line_width=3,
        cursor_proximity_threshold=10,
        objects_opacity=0.9,
        color_fill_opacity=0.1,
        bbox_handler_size=3,
        keypoint_handler_size=5,
    )
    controller = FigureController(AnnotationMode.OBJECT_DETECTION, annotation_style=style)
    controller.set_figures([BBox(20, 20, 40, 40, "car")])

    controller.update_selection(12, 12)

    assert controller.selected_index == 0
    assert controller.figures()[0].active_point_id == 0


def test_keypoint_draw_uses_configured_handler_size(monkeypatch) -> None:
    radii = []

    def fake_circle(frame, center, radius, color, thickness):
        radii.append(radius)
        return frame

    monkeypatch.setattr("annotation_tool.annotation.keypoints.cv2.circle", fake_circle)
    style = AnnotationStyle(
        bbox_line_width=3,
        cursor_proximity_threshold=3,
        objects_opacity=0.9,
        color_fill_opacity=0.1,
        bbox_handler_size=3,
        keypoint_handler_size=11,
    )
    group = KeypointGroup("animal", [Point(5, 5, "head")])

    group.draw(np.zeros((12, 12, 3), dtype=np.uint8), 1.0, None, style)

    assert radii == [11]


def test_mask_draw_uses_configured_fill_opacity() -> None:
    style = AnnotationStyle(
        bbox_line_width=3,
        cursor_proximity_threshold=3,
        objects_opacity=0.9,
        color_fill_opacity=0.25,
        bbox_handler_size=3,
        keypoint_handler_size=5,
    )
    mask = Mask("road", np.ones((1, 1), dtype=np.uint8))
    frame = np.zeros((1, 1, 3), dtype=np.uint8)

    rendered = mask.draw(frame, 1.0, {"road": (0, 0, 100)}, style)

    assert rendered[0, 0, 2] in {24, 25}
