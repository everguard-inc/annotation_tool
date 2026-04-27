from enum import Enum, auto

import cv2
import numpy as np

from annotation_tool.annotation.bboxes import BBox
from annotation_tool.annotation.figures import AnnotationStyle, Figure, Point
from annotation_tool.annotation.keypoints import KeypointGroup
from annotation_tool.annotation.review_labels import ReviewLabel
from annotation_tool.annotation.segmentation import Mask
from annotation_tool.core.enums import AnnotationMode, FigureType
from annotation_tool.core.models import LabelData


class ControllerMode(Enum):
    IDLE = auto()
    CREATE = auto()
    MOVING = auto()


class History:
    def __init__(self) -> None:
        self.items: list[list[Figure]] = []
        self.index = -1

    def add(self, figures: list[Figure]) -> None:
        self.items = self.items[: self.index + 1]
        self.items.append([figure.copy() for figure in figures])
        self.index = len(self.items) - 1

    def previous(self) -> list[Figure] | None:
        if self.index <= 0:
            return None
        self.index -= 1
        return [figure.copy() for figure in self.items[self.index]]

    def next(self) -> list[Figure] | None:
        if self.index >= len(self.items) - 1:
            return None
        self.index += 1
        return [figure.copy() for figure in self.items[self.index]]


class FigureController:
    def __init__(
        self,
        mode: AnnotationMode,
        active_label: LabelData | None = None,
        annotation_style: AnnotationStyle | None = None,
    ) -> None:
        self.mode = mode
        self.active_label = active_label
        self.annotation_style = annotation_style or AnnotationStyle()
        self._figures: list[Figure] = []
        self.buffer: list[Figure] = []
        self.history = History()
        self.controller_mode = ControllerMode.IDLE
        self.start_point: Point | None = None
        self.preview: Figure | None = None
        self.selected_index: int | None = None
        self.cursor = Point(0, 0)
        self.shift_mode = False
        self.polygon: list[tuple[int, int]] = []
        self.image_width = 0
        self.image_height = 0

    def set_figures(self, figures: list[Figure]) -> None:
        self._figures = figures
        self.history.add(self._figures)

    def figures(self) -> list[Figure]:
        return self._figures

    def set_active_label(self, label: LabelData | None) -> None:
        self.active_label = label

        if self.selected_index is None or label is None:
            return

        figure = self._figures[self.selected_index]
        if hasattr(figure, "label") and figure.figure_type == label.type.name:
            figure.label = label.name
            self.history.add(self._figures)

    def handle_mouse_press(self, x: int, y: int) -> None:
        self.cursor = Point(x, y)

        if self.active_label is None:
            return

        if self.mode is AnnotationMode.SEGMENTATION:
            self._handle_segmentation_press(x, y)
            return

        selected, point = self._selected_at(x, y)
        if selected is not None and point is not None:
            self.selected_index = selected
            self._figures[selected].active_point_id = point
            self.controller_mode = ControllerMode.MOVING
            return

        if self.active_label.type is FigureType.REVIEW_LABEL:
            self._figures.append(ReviewLabel(x, y, self.active_label.name))
            self.history.add(self._figures)
            self.update_selection(x, y)
            return

        self.start_point = Point(x, y)
        self.controller_mode = ControllerMode.CREATE

    def handle_mouse_move(self, x: int, y: int) -> None:
        self.cursor = Point(x, y)

        if self.controller_mode is ControllerMode.MOVING and self.selected_index is not None:
            self._figures[self.selected_index].move_active_point(x, y)
            return

        if self.controller_mode is ControllerMode.CREATE and self.start_point:
            self.preview = self._create_figure(self.start_point, Point(x, y))

    def handle_mouse_release(self, x: int, y: int) -> None:
        self.cursor = Point(x, y)

        if self.controller_mode is ControllerMode.MOVING:
            self.controller_mode = ControllerMode.IDLE
            self.history.add(self._figures)
            return

        if self.controller_mode is ControllerMode.CREATE and self.start_point and self.active_label:
            figure = self._create_figure(self.start_point, Point(x, y))
            if figure is not None:
                self._figures.append(figure)
                self.history.add(self._figures)

        self.start_point = None
        self.preview = None
        self.controller_mode = ControllerMode.IDLE
        self.update_selection(x, y)

    def handle_mouse_hover(self, x: int, y: int) -> None:
        self.cursor = Point(x, y)

        if self.mode is AnnotationMode.SEGMENTATION and self.polygon:
            return

        if self.controller_mode is ControllerMode.CREATE and self.start_point:
            self.preview = self._create_figure(self.start_point, Point(x, y))
        else:
            self.update_selection(x, y)

    def delete_selected(self) -> None:
        if self.mode is AnnotationMode.SEGMENTATION and self.active_label:
            mask = self._mask_for_active_label()
            mask.delete_point(None)
            self.history.add(self._figures)
            return

        if self.selected_index is None:
            self.update_selection(self.cursor.x, self.cursor.y)

        if self.selected_index is None:
            return

        figure = self._figures[self.selected_index]
        figure.delete_point(figure.active_point_id)

        if figure.surface <= 0:
            self._figures.pop(self.selected_index)

        self.selected_index = None
        self.history.add(self._figures)

    def delete_all(self) -> None:
        self._figures = []
        self.selected_index = None
        self.history.add(self._figures)

    def copy(self) -> None:
        if self.selected_index is not None:
            self.buffer = [self._figures[self.selected_index].copy()]
        else:
            self.buffer = [figure.copy() for figure in self._figures]

    def paste(self) -> None:
        self._figures.extend(figure.copy() for figure in self.buffer)
        self.history.add(self._figures)

    def undo(self) -> None:
        previous = self.history.previous()
        if previous is not None:
            self._figures = previous
            self.selected_index = None

    def redo(self) -> None:
        next_item = self.history.next()
        if next_item is not None:
            self._figures = next_item
            self.selected_index = None

    def set_shift_mode(self, enabled: bool) -> None:
        self.shift_mode = enabled

    def draw_overlay(self, frame: np.ndarray, scale_factor: float, label_colors: dict | None = None) -> np.ndarray:
        original = frame.copy()
        figures = sorted(self._figures, key=lambda figure: figure.surface, reverse=True)
        for figure in figures:
            frame = figure.draw(
                frame, scale_factor, label_colors, self.annotation_style
            )

        if self.preview is not None:
            frame = self.preview.draw(
                frame, scale_factor, label_colors, self.annotation_style
            )

        if self.mode is AnnotationMode.SEGMENTATION and self.polygon:
            color = (0, 0, 255) if self.shift_mode else (255, 255, 255)
            preview_points = self.polygon + [(self.cursor.x, self.cursor.y)]

            for index in range(len(preview_points) - 1):
                cv2.line(frame, preview_points[index], preview_points[index + 1], color, 1)

            cv2.circle(frame, self.polygon[0], 4, color, 1)

        return cv2.addWeighted(
            frame,
            self.annotation_style.objects_opacity,
            original,
            max(1 - self.annotation_style.objects_opacity, 0),
            0,
        )

    def update_selection(self, x: int, y: int) -> None:
        for figure in self._figures:
            figure.selected = False
            figure.active_point_id = None

        selected, point = self._selected_at(x, y)
        self.selected_index = selected

        if selected is not None:
            self._figures[selected].selected = True
            self._figures[selected].active_point_id = point

    def finish_polygon(self) -> None:
        if self.mode is not AnnotationMode.SEGMENTATION or self.active_label is None:
            return

        if len(self.polygon) < 3:
            self.polygon = []
            return

        mask = self._mask_for_active_label()
        if self.shift_mode:
            mask.remove_polygon(self.polygon)
        else:
            mask.add_polygon(self.polygon)

        self.polygon = []
        self.history.add(self._figures)

    def cancel_polygon(self) -> None:
        self.polygon = []

    def _selected_at(self, x: int, y: int) -> tuple[int | None, int | None]:
        point = Point(x, y)

        for index, figure in sorted(enumerate(self._figures), key=lambda item: item[1].surface):
            point_id = figure.find_nearest_point_index(
                x, y, self.annotation_style.cursor_proximity_threshold
            )
            if point_id is not None:
                return index, point_id
            if figure.contains_point(point):
                return index, None

        return None, None

    def _create_figure(self, start: Point, end: Point) -> Figure | None:
        if self.active_label is None:
            return None

        if self.active_label.type is FigureType.BBOX:
            return BBox.from_points(start, end, self.active_label.name)

        if self.active_label.type is FigureType.KGROUP:
            return KeypointGroup.from_box(start, end, self.active_label.name, self.active_label.attributes or {})

        return None

    def _handle_segmentation_press(self, x: int, y: int) -> None:
        if self.active_label is None:
            return

        if len(self.polygon) >= 3 and Point(*self.polygon[0]).close_to(x, y, 4):
            self.finish_polygon()
            return

        self.polygon.append((x, y))

    def _mask_for_active_label(self) -> Mask:
        assert self.active_label is not None

        for figure in self._figures:
            if isinstance(figure, Mask) and figure.label == self.active_label.name:
                return figure

        mask = Mask.empty(self.active_label.name, self.image_width, self.image_height)
        self._figures.append(mask)
        return mask
