import json
import sqlite3
from pathlib import Path
from typing import Any

from annotation_tool.core.enums import FigureType
from annotation_tool.core.models import LabelData
from annotation_tool.core.paths import LabelingPaths
from annotation_tool.core.utils import read_json, write_json

LABELING_CACHE_MIGRATION_VERSION = 1


class LabelingRepository:
    def __init__(self, data_dir: Path, project_id: int) -> None:
        self.paths = LabelingPaths(data_dir, project_id)

    def get_labels(self) -> list[LabelData]:
        cache = self._cache()
        labels = cache.get("labels", []) + cache.get("review_labels", [])
        return self._sort_labels([self._label_from_dict(item) for item in labels])

    def get_figure_labels(self) -> list[LabelData]:
        cache = self._cache()
        return self._sort_labels(
            [self._label_from_dict(item) for item in cache.get("labels", [])]
        )

    def get_review_labels(self) -> list[LabelData]:
        cache = self._cache()
        return self._sort_labels(
            [self._label_from_dict(item) for item in cache.get("review_labels", [])]
        )

    def save_labels(self, labels: list[LabelData]) -> None:
        cache = self._cache()
        cache["labels"] = [
            self._label_to_dict(label)
            for label in labels
            if label.type != FigureType.REVIEW_LABEL
        ]
        cache["review_labels"] = [
            self._label_to_dict(label)
            for label in labels
            if label.type == FigureType.REVIEW_LABEL
        ]
        self._save_cache(cache)

    def list_image_names(self) -> list[str]:
        cache = self._cache()
        names = [item["name"] for item in cache.get("items", []) if item.get("name")]
        return sorted(names)

    def load_image_annotations(self, image_name: str) -> dict[str, Any]:
        cache = self._cache()
        figures = cache.get("figures", {}).get(image_name, {})
        review = cache.get("review", {}).get(image_name, [])
        return {"figures": figures, "review": review}

    def save_image_annotations(
        self, image_name: str, annotations: dict[str, Any]
    ) -> None:
        cache = self._cache()
        cache.setdefault("figures", {})[image_name] = annotations.get("figures", {})
        cache.setdefault("review", {})[image_name] = annotations.get("review", [])
        self._save_cache(cache)

    def count_review_labels(self) -> int:
        cache = self._cache()
        return sum(len(items) for items in cache.get("review", {}).values())

    def image_path(self, image_name: str) -> Path:
        return self.paths.images_dir / image_name

    def _cache(self) -> dict[str, Any]:
        if self.paths.cache_path.exists():
            return read_json(self.paths.cache_path)

        migrated = self._try_migrate_from_sqlite()
        if migrated is not None:
            write_json(self.paths.cache_path, migrated)
            return migrated

        return {
            "labels": [],
            "review_labels": [],
            "items": [],
            "figures": {},
            "review": {},
        }

    def _save_cache(self, cache: dict[str, Any]) -> None:
        write_json(self.paths.cache_path, cache)

    def _try_migrate_from_sqlite(self) -> dict[str, Any] | None:
        db_path = self.paths.db_path
        if not db_path.exists():
            return None

        try:
            conn = sqlite3.connect(str(db_path))
        except sqlite3.Error:
            return None

        try:
            required = {"label", "image"}
            existing = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if not required.issubset(existing):
                return None

            label_rows = conn.execute(
                "SELECT name, color, hotkey, type, attributes FROM label"
            ).fetchall()
            image_rows = conn.execute(
                "SELECT id, name, height, width, trash, requires_annotation FROM image"
            ).fetchall()

            bbox_rows = (
                conn.execute(
                    "SELECT item_id, x1, y1, x2, y2, label FROM bbox"
                ).fetchall()
                if "bbox" in existing
                else []
            )
            mask_rows = (
                conn.execute("SELECT item_id, label, rle FROM mask").fetchall()
                if "mask" in existing
                else []
            )
            kgroup_rows = (
                conn.execute(
                    "SELECT item_id, label, keypoints_data FROM keypoint_group"
                ).fetchall()
                if "keypoint_group" in existing
                else []
            )
            review_rows = (
                conn.execute("SELECT item_id, x, y, label FROM review_label").fetchall()
                if "review_label" in existing
                else []
            )
        except sqlite3.Error:
            return None
        finally:
            conn.close()

        labels: list[dict[str, Any]] = []
        review_labels: list[dict[str, Any]] = []
        for name, color, hotkey, type_name, attributes in label_rows:
            entry: dict[str, Any] = {
                "name": name,
                "color": color if color is not None else "gray",
                "hotkey": hotkey if hotkey is not None else "",
                "type": type_name if type_name is not None else "BBOX",
            }
            if attributes is not None:
                entry["attributes"] = attributes
            if type_name == FigureType.REVIEW_LABEL.name:
                review_labels.append(entry)
            else:
                labels.append(entry)

        image_by_row_id: dict[int, str] = {}
        items: list[dict[str, Any]] = []
        figures: dict[str, dict[str, Any]] = {}
        for row_id, name, height, width, trash, requires_annotation in image_rows:
            image_by_row_id[row_id] = name
            items.append(
                {
                    "name": name,
                    "height": height,
                    "width": width,
                    "requires_annotation": bool(requires_annotation),
                }
            )
            figures[name] = {
                "trash": bool(trash),
                "bboxes": [],
                "kgroups": [],
                "masks": {},
                "height": height,
                "width": width,
            }

        for item_id, x1, y1, x2, y2, label in bbox_rows:
            image_name = image_by_row_id.get(item_id)
            if image_name is None:
                continue
            figures[image_name]["bboxes"].append(
                {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "label": label}
            )

        for item_id, label, rle in mask_rows:
            image_name = image_by_row_id.get(item_id)
            if image_name is None:
                continue
            figures[image_name]["masks"][label] = str(rle) if rle is not None else ""

        for item_id, label, keypoints_data in kgroup_rows:
            image_name = image_by_row_id.get(item_id)
            if image_name is None:
                continue
            try:
                points = json.loads(keypoints_data) if keypoints_data else []
            except (TypeError, ValueError):
                continue
            if not isinstance(points, list):
                continue
            figures[image_name]["kgroups"].append({"label": label, "points": points})

        review: dict[str, list[dict[str, Any]]] = {}
        for item_id, x, y, label in review_rows:
            image_name = image_by_row_id.get(item_id)
            if image_name is None:
                continue
            review.setdefault(image_name, []).append({"x": x, "y": y, "label": label})

        return {
            "labels": labels,
            "review_labels": review_labels,
            "items": items,
            "figures": figures,
            "review": review,
            "migration_version": LABELING_CACHE_MIGRATION_VERSION,
        }

    def _label_from_dict(self, data: dict[str, Any]) -> LabelData:
        return LabelData(
            name=str(data["name"]),
            color=str(data.get("color", "gray")),
            hotkey=str(data.get("hotkey", "")),
            type=FigureType[str(data.get("type", "BBOX"))],
            attributes=data.get("attributes"),
        )

    def _label_to_dict(self, label: LabelData) -> dict[str, Any]:
        result = {
            "name": label.name,
            "color": label.color,
            "hotkey": label.hotkey,
            "type": label.type.name,
        }
        if label.attributes is not None:
            result["attributes"] = label.attributes
        return result

    def _sort_labels(self, labels: list[LabelData]) -> list[LabelData]:
        return sorted(
            labels,
            key=lambda label: (self._hotkey_sort_value(label.hotkey), label.name),
        )

    def _hotkey_sort_value(self, hotkey: str) -> tuple[int, str]:
        if str(hotkey).isdigit():
            return int(hotkey), ""
        return 10_000, str(hotkey)
