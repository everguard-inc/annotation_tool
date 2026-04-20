import os
from pathlib import Path
from typing import Any

from annotation_tool.core.enums import AnnotationMode
from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import FilteringPaths, LabelingPaths
from annotation_tool.core.utils import image_size, is_valid_json, read_json, write_json
from annotation_tool.infrastructure.file_transfer import FileTransferClient, ProgressCallback
from annotation_tool.infrastructure.unzip import ArchiveUnzipper


class ImportExportService:
    def __init__(
        self,
        data_dir: Path,
        file_transfer: FileTransferClient,
        unzipper: ArchiveUnzipper | None = None,
    ) -> None:
        self.data_dir = data_dir
        self.file_transfer = file_transfer
        self.unzipper = unzipper or ArchiveUnzipper()

    def import_project(self, project: ProjectData, progress: ProgressCallback | None = None) -> None:
        if project.mode is AnnotationMode.FILTERING:
            self.import_filtering_project(project, progress)
        elif project.mode is AnnotationMode.EVENT_VALIDATION:
            return
        else:
            self.import_labeling_project(project, progress)

    def import_labeling_project(self, project: ProjectData, progress: ProgressCallback | None = None) -> None:
        if project.uid is None:
            raise UserVisibleError("Project UID is missing.")

        paths = LabelingPaths(self.data_dir, project.id)
        paths.ensure_project_dir()

        self.file_transfer.download(project.uid, paths.meta_path.name, paths.meta_path, progress=progress)
        self.file_transfer.download(project.uid, paths.figures_path.name, paths.figures_path, progress=progress)
        self.file_transfer.download(project.uid, paths.review_path.name, paths.review_path, progress=progress, ignore_404=True)

        figures = read_json(paths.figures_path)
        expected_images_count = len(figures)

        if not paths.images_dir.exists() or self._images_count(paths.images_dir) != expected_images_count:
            self.file_transfer.download(project.uid, paths.archive_path.name, paths.archive_path, progress=progress)
            self.unzipper.unzip(paths.archive_path, paths.images_dir, progress=progress)
            paths.archive_path.unlink(missing_ok=True)

        actual_images_count = self._images_count(paths.images_dir)
        if actual_images_count != expected_images_count:
            raise UserVisibleError(
                f"Project {project.id} has different number of images and annotations: "
                f"{actual_images_count} images, {expected_images_count} annotations."
            )

        self._build_labeling_cache(paths)

    def import_filtering_project(self, project: ProjectData, progress: ProgressCallback | None = None) -> None:
        if project.uid is None:
            raise UserVisibleError("Project UID is missing.")

        paths = FilteringPaths(self.data_dir, project.id)
        paths.ensure_project_dir()

        self.file_transfer.download(project.uid, paths.video_path.name, paths.video_path, progress=progress)
        self.file_transfer.download(project.uid, paths.meta_path.name, paths.meta_path, progress=progress)

        meta = read_json(paths.meta_path)
        write_json(
            paths.cache_path,
            {
                "labels": meta.get("labels", []),
                "review_labels": meta.get("review_labels", []),
                "items": [],
            },
        )

    def overwrite_annotations(self, project: ProjectData, progress: ProgressCallback | None = None) -> None:
        if project.mode is AnnotationMode.FILTERING:
            raise UserVisibleError("Unable to overwrite annotations for filtering projects.")

        if project.uid is None:
            raise UserVisibleError("Project UID is missing.")

        paths = LabelingPaths(self.data_dir, project.id)
        self.file_transfer.download(project.uid, paths.figures_path.name, paths.figures_path, progress=progress)
        self.file_transfer.download(project.uid, paths.review_path.name, paths.review_path, progress=progress, ignore_404=True)
        self.file_transfer.download(project.uid, paths.meta_path.name, paths.meta_path, progress=progress)

        figures = read_json(paths.figures_path)
        if self._images_count(paths.images_dir) != len(figures):
            raise UserVisibleError(
                f"Project {project.id} has different number of images and annotations after overwrite."
            )

        self._build_labeling_cache(paths)

    def export_figures(self, project: ProjectData) -> Path:
        paths = LabelingPaths(self.data_dir, project.id)
        cache = self._read_cache(paths.cache_path)
        write_json(paths.figures_path, cache.get("figures", {}))
        return paths.figures_path

    def export_review_labels(self, project: ProjectData) -> Path:
        paths = LabelingPaths(self.data_dir, project.id)
        cache = self._read_cache(paths.cache_path)
        write_json(paths.review_path, cache.get("review", {}))
        return paths.review_path

    def export_selected_frames(self, project: ProjectData) -> Path:
        paths = FilteringPaths(self.data_dir, project.id)
        cache = self._read_cache(paths.cache_path)

        result = {"names": [], "ids": []}
        for item in sorted(cache.get("items", []), key=lambda value: value.get("item_id", 0)):
            if not item.get("selected"):
                continue

            if item.get("name"):
                result["names"].append(item["name"])
            elif item.get("item_id") is not None:
                result["ids"].append(item["item_id"])

        write_json(paths.selected_frames_path, result)
        return paths.selected_frames_path

    def export_results(self, project: ProjectData) -> list[Path]:
        if project.mode is AnnotationMode.FILTERING:
            return [self.export_selected_frames(project)]

        return [self.export_figures(project), self.export_review_labels(project)]

    def _build_labeling_cache(self, paths: LabelingPaths) -> None:
        if not is_valid_json(paths.meta_path):
            raise UserVisibleError(f"Invalid JSON: {paths.meta_path}")

        if not is_valid_json(paths.figures_path):
            raise UserVisibleError(f"Invalid JSON: {paths.figures_path}")

        meta = read_json(paths.meta_path)
        figures = read_json(paths.figures_path)
        review = read_json(paths.review_path) if paths.review_path.exists() and is_valid_json(paths.review_path) else {}

        labels = list(meta.get("labels", []))
        review_labels = list(meta.get("review_labels", []))

        labels = self._ensure_blur_label(labels)

        image_names = sorted(name for name in os.listdir(paths.images_dir) if (paths.images_dir / name).is_file())
        items: list[dict[str, Any]] = []

        review_has_items = any(len(value) > 0 for value in review.values())

        for image_name in image_names:
            image_figures = figures.get(image_name, {})
            width = image_figures.get("width")
            height = image_figures.get("height")

            if width is None or height is None:
                width, height = image_size(paths.images_dir / image_name)

            review_items = review.get(image_name, [])

            items.append(
                {
                    "name": image_name,
                    "width": width,
                    "height": height,
                    "requires_annotation": bool(review_items) if review_has_items else True,
                }
            )

        write_json(
            paths.cache_path,
            {
                "labels": labels,
                "review_labels": review_labels,
                "items": items,
                "figures": figures,
                "review": review,
            },
        )

    def _ensure_blur_label(self, labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if any(label.get("name") == "blur" for label in labels):
            return labels

        has_masks = any(label.get("type") == "MASK" for label in labels)
        labels.append(
            {
                "name": "blur",
                "color": "gray",
                "hotkey": "0",
                "type": "MASK" if has_masks else "BBOX",
            }
        )
        return labels

    def _images_count(self, images_dir: Path) -> int:
        if not images_dir.exists():
            return 0
        return len([path for path in images_dir.iterdir() if path.is_file()])

    def _read_cache(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        return read_json(path)
