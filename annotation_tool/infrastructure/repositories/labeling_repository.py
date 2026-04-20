from pathlib import Path
from typing import Any

from annotation_tool.core.enums import FigureType
from annotation_tool.core.models import LabelData
from annotation_tool.core.paths import LabelingPaths
from annotation_tool.core.utils import read_json, write_json


class LabelingRepository:
    def __init__(self, data_dir: Path, project_id: int) -> None:
        self.paths = LabelingPaths(data_dir, project_id)

    def get_labels(self) -> list[LabelData]:
        cache = self._cache()
        labels = cache.get("labels", []) + cache.get("review_labels", [])
        return self._sort_labels([self._label_from_dict(item) for item in labels])

    def get_figure_labels(self) -> list[LabelData]:
        cache = self._cache()
        return self._sort_labels([self._label_from_dict(item) for item in cache.get("labels", [])])

    def get_review_labels(self) -> list[LabelData]:
        cache = self._cache()
        return self._sort_labels([self._label_from_dict(item) for item in cache.get("review_labels", [])])

    def save_labels(self, labels: list[LabelData]) -> None:
        cache = self._cache()
        cache["labels"] = [self._label_to_dict(label) for label in labels if label.type != FigureType.REVIEW_LABEL]
        cache["review_labels"] = [self._label_to_dict(label) for label in labels if label.type == FigureType.REVIEW_LABEL]
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

    def save_image_annotations(self, image_name: str, annotations: dict[str, Any]) -> None:
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
        if not self.paths.cache_path.exists():
            return {"labels": [], "review_labels": [], "items": [], "figures": {}, "review": {}}
        return read_json(self.paths.cache_path)

    def _save_cache(self, cache: dict[str, Any]) -> None:
        write_json(self.paths.cache_path, cache)

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
        return sorted(labels, key=lambda label: (self._hotkey_sort_value(label.hotkey), label.name))

    def _hotkey_sort_value(self, hotkey: str) -> tuple[int, str]:
        if str(hotkey).isdigit():
            return int(hotkey), ""
        return 10_000, str(hotkey)
