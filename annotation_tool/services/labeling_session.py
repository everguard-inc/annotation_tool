from copy import deepcopy

import cv2
import numpy as np

from annotation_tool.annotation.bboxes import BBox
from annotation_tool.annotation.figure_controller import FigureController
from annotation_tool.annotation.figure_controller_factory import FigureControllerFactory
from annotation_tool.annotation.figures import AnnotationStyle, Figure, Point
from annotation_tool.annotation.keypoints import KeypointGroup
from annotation_tool.annotation.masks_encoding import decode_rle
from annotation_tool.annotation.review_labels import ReviewLabel
from annotation_tool.annotation.segmentation import Mask
from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import LabelData, LabelingStatusData, ProjectData
from annotation_tool.infrastructure.repositories.labeling_repository import (
    LabelingRepository,
)
from annotation_tool.media.image_converter import deteriorate_image
from annotation_tool.services.session_state import SessionState, SessionStateStore
from annotation_tool.services.statistics_service import StatisticsService


class LabelingSession:
    def __init__(
        self,
        project: ProjectData,
        repository: LabelingRepository,
        session_state_store: SessionStateStore | None = None,
        statistics_service: StatisticsService | None = None,
        annotation_style: AnnotationStyle | None = None,
    ) -> None:
        self.project = project
        self.repository = repository
        self.session_state_store = session_state_store
        self.statistics_service = statistics_service
        self.annotation_style = annotation_style or AnnotationStyle()
        self.image_names = self._filtered_image_names()

        if session_state_store is not None:
            state = session_state_store.load()
            self.item_id = min(state.item_id, max(len(self.image_names) - 1, 0))
            self.duration_hours = state.duration_hours
            self.processed_item_ids = set(state.processed_item_ids)
        else:
            self.item_id = 0
            self.duration_hours = 0.0
            self.processed_item_ids = set()
        if self.statistics_service is not None:
            self.statistics_service.duration_hours = self.duration_hours

        self.hide_figures = False
        self.hide_review_labels = False
        self.show_label_names = False
        self.show_object_size = False
        self.make_image_worse = False

        self.cursor_x = 0
        self.cursor_y = 0
        self.scale_factor = 1.0

        self.figure_labels = repository.get_figure_labels()
        self.review_labels = repository.get_review_labels()
        self.available_labels = (
            self.review_labels
            if project.stage is AnnotationStage.REVIEW
            else self.figure_labels
        )
        self.active_label = self._default_active_label(self.available_labels)

        self.controller: FigureController = FigureControllerFactory().create(
            project.mode, self.active_label, self.annotation_style
        )
        self.review_figures: list[ReviewLabel] = []

        self.load_current_item()

    def item_count(self) -> int:
        return len(self.image_names)

    def current_item_id(self) -> int:
        return self.item_id

    def current_image_path(self) -> str:
        return str(self.repository.image_path(self.image_names[self.item_id]))

    def labels(self) -> list[LabelData]:
        return self.available_labels

    def status(self) -> LabelingStatusData:
        selected_class = ""
        class_color = "gray"

        if self.active_label is not None:
            selected_class = f"{self.active_label.name}: {self.active_label.type.name} [{self.active_label.hotkey}]"
            class_color = self.active_label.color

        is_trash = False
        if self.project.stage is not AnnotationStage.REVIEW:
            is_trash = self._current_figures_dict().get("trash", False)

        return LabelingStatusData(
            item_id=self.item_id,
            items_count=max(self.item_count(), 1),
            duration_hours=self.duration_hours,
            speed_per_hour=round(
                len(self.processed_item_ids) / (self.duration_hours + 1e-7), 2
            ),
            processed_count=len(self.processed_item_ids),
            selected_class=selected_class,
            class_color=class_color,
            is_trash=is_trash,
            annotation_mode=self.project.mode.name,
            annotation_stage=self.project.stage.name,
            figures_hidden=self.hide_figures,
            review_labels_hidden=self.hide_review_labels,
        )

    def render_frame(self) -> np.ndarray:
        frame = cv2.imread(self.current_image_path())
        if frame is None:
            raise RuntimeError(f"Unable to read image: {self.current_image_path()}")

        if self.make_image_worse:
            frame = deteriorate_image(frame)

        self._apply_display_flags()
        label_colors = self._label_colors()

        if not self.hide_figures:
            frame = self._draw_figures_with_blur(frame, label_colors)

        if (
            not self.hide_review_labels
            and self.project.stage is not AnnotationStage.REVIEW
        ):
            for review_label in self.review_figures:
                frame = review_label.draw(
                    frame, self.scale_factor, label_colors, self.annotation_style
                )

        if self.project.mode is AnnotationMode.OBJECT_DETECTION:
            frame = self._draw_crosshair(frame)

        return frame

    def reload_labels(self) -> None:
        """Re-read the label catalogue after an external cache.json
        mutation (download-and-overwrite). Without this, figure_labels /
        review_labels / available_labels / active_label stay frozen at the
        values captured in __init__, so the UI keeps the old class chips
        and active_label even after the underlying catalogue changed."""
        previous_active_name = (
            self.active_label.name if self.active_label is not None else None
        )

        self.figure_labels = self.repository.get_figure_labels()
        self.review_labels = self.repository.get_review_labels()
        self.available_labels = (
            self.review_labels
            if self.project.stage is AnnotationStage.REVIEW
            else self.figure_labels
        )

        matched = None
        if previous_active_name is not None:
            matched = next(
                (
                    label
                    for label in self.available_labels
                    if label.name == previous_active_name
                ),
                None,
            )
        self.active_label = matched or self._default_active_label(self.available_labels)

    def apply_annotation_style(self, style: AnnotationStyle) -> None:
        self.annotation_style = style
        self.controller.annotation_style = style

    def load_current_item(self) -> None:
        if not self.image_names:
            return

        annotations = self.repository.load_image_annotations(
            self.image_names[self.item_id]
        )
        figures = annotations.get("figures", {})
        review = annotations.get("review", [])

        if self.project.stage is AnnotationStage.REVIEW:
            self.controller = FigureControllerFactory().create(
                AnnotationMode.OBJECT_DETECTION,
                self.active_label,
                self.annotation_style,
            )
            self.controller.set_figures(
                [ReviewLabel(item["x"], item["y"], item["label"]) for item in review]
            )
            self.review_figures = []
        else:
            self.controller = FigureControllerFactory().create(
                self.project.mode,
                self.active_label,
                self.annotation_style,
            )
            self.controller.set_figures(self._figures_from_dict(figures))
            self.review_figures = [
                ReviewLabel(item["x"], item["y"], item["label"]) for item in review
            ]

        image = cv2.imread(self.current_image_path())
        if image is not None:
            self.controller.image_height, self.controller.image_width = image.shape[:2]

    def save_current_item(self) -> None:
        if not self.image_names:
            return

        image_name = self.image_names[self.item_id]
        annotations = self.repository.load_image_annotations(image_name)

        if self.project.stage is AnnotationStage.REVIEW:
            annotations["review"] = [
                figure.serialize() for figure in self.controller.figures()
            ]
        else:
            previous = annotations.get("figures", {})
            saved = self._figures_to_dict(self.controller.figures())
            saved["trash"] = previous.get("trash", False)
            annotations["figures"] = saved

        self.repository.save_image_annotations(image_name, annotations)

    def _persist_session_state(self) -> None:
        if self.session_state_store is None:
            return
        self.session_state_store.save(
            SessionState(
                item_id=self.item_id,
                duration_hours=self.duration_hours,
                processed_item_ids=set(self.processed_item_ids),
            )
        )

    def _track_action(self, message: str) -> None:
        if self.statistics_service is None:
            return
        self.duration_hours = self.statistics_service.track_action(
            self.project.stage, message
        )
        self._persist_session_state()

    def go_to_item(self, item_id: int) -> None:
        if not self.image_names:
            return

        self._track_action("keyboard")
        self.save_current_item()
        self.processed_item_ids.add(self.item_id)
        self.item_id = max(0, min(item_id, self.item_count() - 1))
        self.load_current_item()
        self._persist_session_state()

    def next_item(self) -> None:
        self.go_to_item(self.item_id + 1)

    def previous_item(self) -> None:
        self.go_to_item(self.item_id - 1)

    def set_active_label_by_hotkey(self, hotkey: str) -> None:
        for label in self.available_labels:
            if label.hotkey == hotkey:
                self._track_action("keyboard")
                self.active_label = label
                self.controller.set_active_label(label)
                return

    def toggle_trash(self) -> None:
        if self.project.stage is AnnotationStage.REVIEW:
            return

        self._track_action("keyboard")
        annotations = self.repository.load_image_annotations(
            self.image_names[self.item_id]
        )
        figures = annotations.get("figures", {})
        figures["trash"] = not figures.get("trash", False)
        annotations["figures"] = figures
        self.repository.save_image_annotations(
            self.image_names[self.item_id], annotations
        )

    def toggle_figures_visibility(self) -> None:
        self._track_action("keyboard")
        self.hide_figures = not self.hide_figures

    def toggle_review_labels_visibility(self) -> None:
        self._track_action("keyboard")
        self.hide_review_labels = not self.hide_review_labels

    def toggle_label_names(self) -> None:
        self._track_action("keyboard")
        self.show_label_names = not self.show_label_names

    def toggle_object_size(self) -> None:
        self._track_action("keyboard")
        self.show_object_size = not self.show_object_size

    def toggle_degraded_preview(self) -> None:
        self._track_action("keyboard")
        self.make_image_worse = not self.make_image_worse

    def set_shift_mode(self, enabled: bool) -> None:
        self.controller.set_shift_mode(enabled)

    def set_cursor(self, x: int, y: int) -> None:
        self.cursor_x = x
        self.cursor_y = y
        self.controller.cursor = Point(x, y)

    def editing_blocked(self) -> bool:
        return (
            self.hide_figures and self.project.mode is not AnnotationMode.SEGMENTATION
        )

    def handle_mouse_press(self, x: int, y: int) -> None:
        self._track_action("lmp")
        if not self.editing_blocked():
            self.controller.handle_mouse_press(x, y)

    def handle_mouse_move(self, x: int, y: int) -> None:
        if not self.editing_blocked():
            self.controller.handle_mouse_move(x, y)

    def handle_mouse_release(self, x: int, y: int) -> None:
        if not self.editing_blocked():
            self.controller.handle_mouse_release(x, y)

    def handle_mouse_hover(self, x: int, y: int) -> None:
        self.controller.handle_mouse_hover(x, y)

    def delete_selected(self) -> None:
        self._track_action("keyboard")
        if not self.editing_blocked():
            self.controller.delete_selected()

    def delete_all(self) -> None:
        self._track_action("keyboard")
        if not self.editing_blocked():
            self.controller.delete_all()

    def copy(self) -> None:
        self._track_action("keyboard")
        if not self.editing_blocked():
            self.controller.copy()

    def paste(self) -> None:
        self._track_action("keyboard")
        if not self.editing_blocked():
            self.controller.paste()

    def undo(self) -> None:
        self._track_action("keyboard")
        if not self.editing_blocked():
            self.controller.undo()

    def redo(self) -> None:
        self._track_action("keyboard")
        if not self.editing_blocked():
            self.controller.redo()

    def finish_polygon(self) -> None:
        self._track_action("keyboard")
        self.controller.finish_polygon()

    def cancel_polygon(self) -> None:
        self._track_action("keyboard")
        self.controller.cancel_polygon()

    def copy_from_previous_item(self) -> None:
        if self.item_id == 0 or self.editing_blocked():
            return

        self._track_action("keyboard")
        current_name = self.image_names[self.item_id]
        previous_name = self.image_names[self.item_id - 1]
        current_annotations = self.repository.load_image_annotations(current_name)
        previous_annotations = self.repository.load_image_annotations(previous_name)

        if self.project.stage is AnnotationStage.REVIEW:
            current_annotations["review"] = deepcopy(
                previous_annotations.get("review", [])
            )
        else:
            current_figures = current_annotations.get("figures", {})
            previous_figures = previous_annotations.get("figures", {})
            current_figures["bboxes"] = deepcopy(previous_figures.get("bboxes", []))
            current_figures["kgroups"] = deepcopy(previous_figures.get("kgroups", []))
            current_figures["masks"] = deepcopy(previous_figures.get("masks", {}))
            current_annotations["figures"] = current_figures

        self.repository.save_image_annotations(current_name, current_annotations)
        self.load_current_item()

    def close(self) -> None:
        self.save_current_item()
        self._persist_session_state()

    def _filtered_image_names(self) -> list[str]:
        names = self.repository.list_image_names()

        if self.project.stage not in {
            AnnotationStage.REVIEW,
            AnnotationStage.CORRECTION,
        }:
            return names

        cache = self.repository._cache()

        if self.project.stage is AnnotationStage.REVIEW:
            allowed = {
                item["name"]
                for item in cache.get("items", [])
                if item.get("requires_annotation") and item.get("name")
            }
            return [name for name in names if name in allowed]

        review = cache.get("review", {})
        return [name for name in names if review.get(name)]

    def _figures_from_dict(self, figures: dict) -> list[Figure]:
        result: list[Figure] = []

        for item in figures.get("bboxes", []):
            result.append(
                BBox(item["x1"], item["y1"], item["x2"], item["y2"], item["label"])
            )

        for item in figures.get("kgroups", []):
            label = self._label_by_name(item["label"])
            points_data = item.get("points", [])
            points = [
                Point(point["x"], point["y"], point.get("label"))
                for point in points_data
            ]
            result.append(
                KeypointGroup(
                    item["label"], points, label.attributes if label else None
                )
            )

        width = figures.get("width", 0)
        height = figures.get("height", 0)
        for label, rle in figures.get("masks", {}).items():
            result.append(Mask(label, decode_rle(rle, width=width, height=height)))

        return result

    def _figures_to_dict(self, figures: list[Figure]) -> dict:
        bboxes = []
        kgroups = []
        masks = {}

        width = height = 0
        image = cv2.imread(self.current_image_path())
        if image is not None:
            height, width = image.shape[:2]

        for figure in figures:
            if isinstance(figure, BBox):
                bboxes.append(figure.serialize())
            elif isinstance(figure, KeypointGroup):
                kgroups.append(figure.serialize())
            elif isinstance(figure, Mask):
                masks[figure.label] = figure.serialize()["rle"]

        return {
            "trash": False,
            "bboxes": bboxes,
            "kgroups": kgroups,
            "masks": masks,
            "height": height,
            "width": width,
        }

    def _default_active_label(self, labels: list[LabelData]) -> LabelData | None:
        if not labels:
            return None
        for label in labels:
            if label.name != "blur":
                return label
        return labels[0]

    def _draw_figures_with_blur(
        self, frame: np.ndarray, label_colors: dict[str, tuple[int, int, int]]
    ) -> np.ndarray:
        figures = self.controller.figures()
        blur_figures = [
            figure for figure in figures if getattr(figure, "label", None) == "blur"
        ]

        if not blur_figures:
            return self.controller.draw_overlay(frame, self.scale_factor, label_colors)

        frame = self._apply_blur_figures(frame, blur_figures)
        original_figures = self.controller._figures
        self.controller._figures = [
            figure
            for figure in original_figures
            if getattr(figure, "label", None) != "blur" or figure.selected
        ]
        try:
            return self.controller.draw_overlay(frame, self.scale_factor, label_colors)
        finally:
            self.controller._figures = original_figures

    def _apply_blur_figures(
        self, frame: np.ndarray, blur_figures: list[Figure]
    ) -> np.ndarray:
        blurred = cv2.GaussianBlur(frame, (31, 31), sigmaX=0)
        height, width = frame.shape[:2]

        for figure in blur_figures:
            if isinstance(figure, BBox):
                x1 = max(0, min(figure.x1, width - 1))
                x2 = max(0, min(figure.x2, width - 1))
                y1 = max(0, min(figure.y1, height - 1))
                y2 = max(0, min(figure.y2, height - 1))
                frame[y1 : y2 + 1, x1 : x2 + 1] = blurred[y1 : y2 + 1, x1 : x2 + 1]
            elif isinstance(figure, Mask):
                mask = figure.mask.astype(bool)
                if mask.shape == frame.shape[:2]:
                    frame[mask] = blurred[mask]

        return frame

    def _apply_display_flags(self) -> None:
        for figure in self.controller.figures():
            if isinstance(figure, BBox):
                figure.show_label = self.show_label_names
                figure.show_size = self.show_object_size
            elif isinstance(figure, KeypointGroup):
                figure.show_names = self.show_label_names

    def _current_figures_dict(self) -> dict:
        annotations = self.repository.load_image_annotations(
            self.image_names[self.item_id]
        )
        return annotations.get("figures", {})

    def _label_by_name(self, name: str) -> LabelData | None:
        for label in self.repository.get_labels():
            if label.name == name:
                return label
        return None

    def _label_colors(self) -> dict[str, tuple[int, int, int]]:
        color_map = {
            "red": (0, 0, 255),
            "lime": (0, 255, 0),
            "green": (0, 128, 0),
            "blue": (255, 0, 0),
            "yellow": (0, 255, 255),
            "cyan": (255, 255, 0),
            "magenta": (255, 0, 255),
            "gray": (192, 192, 192),
            "white": (255, 255, 255),
        }
        return {
            label.name: color_map.get(label.color, color_map["gray"])
            for label in self.repository.get_labels()
        }

    def _draw_crosshair(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        x = max(0, min(self.cursor_x, w - 1))
        y = max(0, min(self.cursor_y, h - 1))
        cv2.line(frame, (x, 0), (x, h), (255, 255, 255), 1)
        cv2.line(frame, (0, y), (w, y), (255, 255, 255), 1)
        return frame
