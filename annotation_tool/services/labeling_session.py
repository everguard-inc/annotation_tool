import cv2
import numpy as np

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
        self.shift_mode = False

        self.cursor_x = 0
        self.cursor_y = 0
        self.scale_factor = 1.0

        self.figure_labels = repository.get_figure_labels()
        self.review_labels = repository.get_review_labels()
        self.available_labels = self.review_labels if project.stage is AnnotationStage.REVIEW else self.figure_labels
        self.active_label = self.available_labels[0] if self.available_labels else None

    def item_count(self) -> int:
        return len(self.image_names)

    def current_item_id(self) -> int:
        return self.item_id

    def current_image_path(self) -> str:
        return str(self.repository.image_path(self.image_names[self.item_id]))

    def labels(self) -> list[LabelData]:
        return self.available_labels

    def status(self) -> LabelingStatusData:
        active_label = self.active_label
        selected_class = ""
        class_color = "gray"

        if active_label is not None:
            selected_class = f"{active_label.name}: {active_label.type.name} [{active_label.hotkey}]"
            class_color = active_label.color

        return LabelingStatusData(
            item_id=self.item_id,
            items_count=max(self.item_count(), 1),
            duration_hours=self.duration_hours,
            speed_per_hour=round(len(self.processed_item_ids) / (self.duration_hours + 1e-7), 2),
            processed_count=len(self.processed_item_ids),
            selected_class=selected_class,
            class_color=class_color,
            is_trash=self._current_figures().get("trash", False),
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

        if not self.hide_figures:
            frame = self._draw_figures(frame)

        if not self.hide_review_labels:
            frame = self._draw_review_labels(frame)

        frame = self._draw_crosshair(frame)
        return frame

    def load_current_item(self) -> None:
        self.render_frame()

    def save_current_item(self) -> None:
        pass

    def go_to_item(self, item_id: int) -> None:
        if not self.image_names:
            return

        self.save_current_item()
        self.processed_item_ids.add(self.item_id)
        self.item_id = max(0, min(item_id, self.item_count() - 1))

    def next_item(self) -> None:
        self.go_to_item(self.item_id + 1)

    def previous_item(self) -> None:
        self.go_to_item(self.item_id - 1)

    def set_active_label_by_hotkey(self, hotkey: str) -> None:
        for label in self.available_labels:
            if label.hotkey == hotkey:
                self.active_label = label
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
        self.shift_mode = enabled

    def set_cursor(self, x: int, y: int) -> None:
        self.cursor_x = x
        self.cursor_y = y

    def editing_blocked(self) -> bool:
        return self.hide_figures and self.project.mode is not AnnotationMode.SEGMENTATION

    def copy_from_previous_item(self) -> None:
        if self.item_id == 0 or self.editing_blocked():
            return

        current_name = self.image_names[self.item_id]
        previous_name = self.image_names[self.item_id - 1]
        annotations = self.repository.load_image_annotations(previous_name)
        self.repository.save_image_annotations(current_name, annotations)

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

    def _current_figures(self) -> dict:
        annotations = self.repository.load_image_annotations(self.image_names[self.item_id])
        return annotations.get("figures", {})

    def _draw_figures(self, frame: np.ndarray) -> np.ndarray:
        figures = self._current_figures()

        for bbox in figures.get("bboxes", []):
            x1, y1, x2, y2 = int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])
            color = self._color_by_label_name(bbox.get("label"))
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            if self.show_label_names:
                cv2.putText(frame, str(bbox.get("label", "")), (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            if self.show_object_size:
                text = f"{abs(y2 - y1)}x{abs(x2 - x1)}"
                cv2.putText(frame, text, (x1, min(frame.shape[0] - 5, y2 + 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        for label, rle in figures.get("masks", {}).items():
            color = self._color_by_label_name(label)
            frame = self._draw_mask_placeholder(frame, color)

        return frame

    def _draw_review_labels(self, frame: np.ndarray) -> np.ndarray:
        annotations = self.repository.load_image_annotations(self.image_names[self.item_id])

        for item in annotations.get("review", []):
            x, y = int(item["x"]), int(item["y"])
            label = str(item.get("label", ""))
            color = self._color_by_label_name(label)
            cv2.circle(frame, (x, y), 5, color, -1)
            cv2.putText(frame, label, (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return frame

    def _draw_crosshair(self, frame: np.ndarray) -> np.ndarray:
        if self.project.mode is not AnnotationMode.OBJECT_DETECTION:
            return frame

        h, w = frame.shape[:2]
        x = max(0, min(self.cursor_x, w - 1))
        y = max(0, min(self.cursor_y, h - 1))
        cv2.line(frame, (x, 0), (x, h), (255, 255, 255), 1)
        cv2.line(frame, (0, y), (w, y), (255, 255, 255), 1)
        return frame

    def _draw_mask_placeholder(self, frame: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
        overlay = frame.copy()
        overlay[:, :, :] = color
        return cv2.addWeighted(overlay, 0.08, frame, 0.92, 0)

    def _color_by_label_name(self, name: str | None) -> tuple[int, int, int]:
        colors = {
            "red": (0, 0, 255),
            "lime": (0, 255, 0),
            "blue": (255, 0, 0),
            "yellow": (0, 255, 255),
            "cyan": (255, 255, 0),
            "magenta": (255, 0, 255),
            "gray": (192, 192, 192),
            "green": (0, 128, 0),
        }

        for label in self.repository.get_labels():
            if label.name == name:
                return colors.get(label.color, colors["gray"])

        return colors["gray"]
