from pathlib import Path
from typing import Any

from annotation_tool.core.paths import FilteringPaths
from annotation_tool.core.utils import read_json, write_json


class FilteringRepository:
    def __init__(self, data_dir: Path, project_id: int) -> None:
        self.paths = FilteringPaths(data_dir, project_id)
        self._cache_data: dict[str, Any] | None = None
        self._dirty = False

    def get_selected(self, item_id: int, name: str | None = None) -> bool:
        item = self._find_or_create_item(item_id, name)
        return bool(item.get("selected", False))

    def set_selected(self, item_id: int, name: str | None, selected: bool) -> None:
        cache = self._cache()
        item = self._find_or_create_item_in_cache(cache, item_id, name)
        item["selected"] = selected
        self._dirty = True
        self.flush()

    def toggle_selected(self, item_id: int, name: str | None) -> bool:
        selected = not self.get_selected(item_id, name)
        self.set_selected(item_id, name, selected)
        return selected

    def list_selected(self) -> list[tuple[int | None, str | None]]:
        result = []
        for item in self._cache().get("items", []):
            if item.get("selected"):
                result.append((item.get("item_id"), item.get("name")))
        return result

    def count_selected(self) -> int:
        return len(self.list_selected())

    def list_items(self) -> list[dict[str, Any]]:
        return sorted(self._cache().get("items", []), key=lambda item: item.get("item_id", 0))

    def save_item_name(self, item_id: int, name: str | None) -> None:
        cache = self._cache()
        item = self._find_or_create_item_in_cache(cache, item_id, name)

        if name is not None and item.get("name") != name:
            item["name"] = name
            self._dirty = True

    def flush(self) -> None:
        if self._dirty and self._cache_data is not None:
            write_json(self.paths.cache_path, self._cache_data)
            self._dirty = False

    def _find_or_create_item(self, item_id: int, name: str | None) -> dict[str, Any]:
        cache = self._cache()
        return self._find_or_create_item_in_cache(cache, item_id, name)

    def _find_or_create_item_in_cache(self, cache: dict[str, Any], item_id: int, name: str | None) -> dict[str, Any]:
        cache.setdefault("items", [])

        for item in cache["items"]:
            if item.get("item_id") == item_id:
                return item

        item = {"item_id": item_id, "name": name, "selected": False}
        cache["items"].append(item)
        self._dirty = True
        return item

    def _cache(self) -> dict[str, Any]:
        if self._cache_data is not None:
            return self._cache_data

        if not self.paths.cache_path.exists():
            self._cache_data = {"labels": [], "review_labels": [], "items": []}
            self._dirty = True
            return self._cache_data

        self._cache_data = read_json(self.paths.cache_path)
        return self._cache_data
