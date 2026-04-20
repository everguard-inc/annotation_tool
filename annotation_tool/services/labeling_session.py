import cv2
import numpy as np

from annotation_tool.annotation.bboxes import BBox
from annotation_tool.annotation.figure_controller import FigureController
from annotation_tool.annotation.figure_controller_factory import FigureControllerFactory
from annotation_tool.annotation.figures import Figure, Point
from annotation_tool.annotation.keypoints import KeypointGroup
from annotation_tool.annotation.masks_encoding import decode_rle
from annotation_tool.annotation.review_labels import ReviewLabel
from annotation_tool.annotation.segmentation import Mask
from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import LabelData, LabelingStatusData, ProjectData
from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.media.image_converter import deteriorate_image


class LabelingSession:
    def __init__(self, project: ProjectData, repository: LabelingRepository) -> None:
        self.project = project
        self.repository = repository
        self.image_names = self._filtered_image_names()
        self.item_id = 0
        self.duration_hours = 0.0
        self.processed_item_ids: set[int] = set()

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
        self.available_labels = self.review_labels if project.stage is AnnotationStage.REVIEW else self.figure_labels
        self.active_label = self.available_labels[0] if self.available_labels else None

        self.controller: FigureController = FigureControllerFactory().create(project.mode, self.active_label)
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
            speed_per_hour=round(len(self.processed_item_ids) / (self.duration_hours + 1e-7), 2),
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
            frame = self.controller.draw_overlay(frame, self.scale_factor, label_colors)

        if not self.hide_review_labels and self.project.stage is not AnnotationStage.REVIEW:
            for review_label in self.review_figures:
                frame = review_label.draw(frame, self.scale_factor, label_colors)

        if self.project.mode is AnnotationMode.OBJECT_DETECTION:
            frame = self._draw_crosshair(frame)

        return frame

    def load_current_item(self) -> None:
        if not self.image_names:
            return

        annotations = self.repository.load_image_annotations(self.image_names[self.item_id])
        figures = annotations.get("figures", {})
        review = annotations.get("review", [])

        if self.project.stage is AnnotationStage.REVIEW:
            self.controller = FigureControllerFactory().create(AnnotationMode.OBJECT_DETECTION, self.active_label)
            self.controller.set_figures([ReviewLabel(item["x"], item["y"], item["label"]) for item in review])
            self.review_figures = []
        else:
            self.controller = FigureControllerFactory().create(self.project.mode, self.active_label)
            self.controller.set_figures(self._figures_from_dict(figures))
            self.review_figures = [ReviewLabel(item["x"], item["y"], item["label"]) for item in review]

        image = cv2.imread(self.current_image_path())
        if image is not None:
            self.controller.image_height, self.controller.image_width = image.shape[:2]

    def save_current_item(self) -> None:
        if not self.image_names:
            return

        image_name = self.image_names[self.item_id]
        annotations = self.repository.load_image_annotations(image_name)

        if self.project.stage is AnnotationStage.REVIEW:
            annotations["review"] = [figure.serialize() for figure in self.controller.figures()]
        else:
            previous = annotations.get("figures", {})
            saved = self._figures_to_dict(self.controller.figures())
            saved["trash"] = previous.get("trash", False)
            annotations["figures"] = saved

        self.repository.save_image_annotations(image_name, annotations)

    def go_to_item(self, item_id: int) -> None:
        if not self.image_names:
            return

        self.save_current_item()
        self.processed_item_ids.add(self.item_id)
        self.item_id = max(0, min(item_id, self.item_count() - 1))
        self.load_current_item()

    def next_item(self) -> None:
        self.go_to_item(self.item_id + 1)

    def previous_item(self) -> None:
        self.go_to_item(self.item_id - 1)

    def set_active_label_by_hotkey(self, hotkey: str) -> None:
        for label in self.available_labels:
            if label.hotkey == hotkey:
                self.active_label = label
                self.controller.set_active_label(label)
                return

    def toggle_trash(self) -> None:
        if self.project.stage is AnnotationStage.REVIEW:
            return

        annotations = self.repository.load_image_annotations(self.image_names[self.item_id])
        figures = annotations.get("figures", {})
        figures["trash"] = not figures.get("trash", False)
        annotations["figures"] = figures
        self.repository.save_image_annotations(self.image_names[self.item_id], annotations)

    def toggle_figures_visibility(self) -> None:
        self.hide_figures = not self.hide_figures

    def toggle_review_labels_visibility(self) -> None:
        self.hide_review_labels = not self.hide_review_labels

    def toggle_label_names(self) -> None:
        self.show_label_names = not self.show_label_names

    def toggle_object_size(self) -> None:
        self.show_object_size = not self.show_object_size

    def toggle_degraded_preview(self) -> None:
        self.make_image_worse = not self.make_image_worse

    def set_shift_mode(self, enabled: bool) -> None:
        self.controller.set_shift_mode(enabled)

    def set_cursor(self, x: int, y: int) -> None:
        self.cursor_x = x
        self.cursor_y = y
        self.controller.cursor = Point(x, y)

    def editing_blocked(self) -> bool:
        return self.hide_figures and self.project.mode is not AnnotationMode.SEGMENTATION

    def handle_mouse_press(self, x: int, y: int) -> None:
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
        if not self.editing_blocked():
            self.controller.delete_selected()

    def delete_all(self) -> None:
        if not self.editing_blocked():
            self.controller.delete_all()

    def copy(self) -> None:
        if not self.editing_blocked():
            self.controller.copy()

    def paste(self) -> None:
        if not self.editing_blocked():
            self.controller.paste()

    def undo(self) -> None:
        if not self.editing_blocked():
            self.controller.undo()

    def redo(self) -> None:
        if not self.editing_blocked():
            self.controller.redo()

    def finish_polygon(self) -> None:
        self.controller.finish_polygon()

    def cancel_polygon(self) -> None:
        self.controller.cancel_polygon()

    def copy_from_previous_item(self) -> None:
        if self.item_id == 0 or self.editing_blocked():
            return

        current_name = self.image_names[self.item_id]
        previous_name = self.image_names[self.item_id - 1]
        annotations = self.repository.load_image_annotations(previous_name)
        self.repository.save_image_annotations(current_name, annotations)
        self.load_current_item()

    def close(self) -> None:
        self.save_current_item()

    def _filtered_image_names(self) -> list[str]:
        names = self.repository.list_image_names()

        if self.project.stage not in {AnnotationStage.REVIEW, AnnotationStage.CORRECTION}:
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
            result.append(BBox(item["x1"], item["y1"], item["x2"], item["y2"], item["label"]))

        for item in figures.get("kgroups", []):
            label = self._label_by_name(item["label"])
            points_data = item.get("points", [])
            points = [Point(point["x"], point["y"], point.get("label")) for point in points_data]
            result.append(KeypointGroup(item["label"], points, label.attributes if label else None))

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

    def _apply_display_flags(self) -> None:
        for figure in self.controller.figures():
            if isinstance(figure, BBox):
                figure.show_label = self.show_label_names
                figure.show_size = self.show_object_size
            elif isinstance(figure, KeypointGroup):
                figure.show_names = self.show_label_names

    def _current_figures_dict(self) -> dict:
        annotations = self.repository.load_image_annotations(self.image_names[self.item_id])
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
        return {label.name: color_map.get(label.color, color_map["gray"]) for label in self.repository.get_labels()}

    def _draw_crosshair(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        x = max(0, min(self.cursor_x, w - 1))
        y = max(0, min(self.cursor_y, h - 1))
        cv2.line(frame, (x, 0), (x, h), (255, 255, 255), 1)
        cv2.line(frame, (0, y), (w, y), (255, 255, 255), 1)
        return frame
