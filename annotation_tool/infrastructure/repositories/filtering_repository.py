import sqlite3
from pathlib import Path
from typing import Any

from annotation_tool.core.paths import FilteringPaths
from annotation_tool.core.utils import read_json, write_json

FILTERING_CACHE_MIGRATION_VERSION = 1


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
        return sorted(
            result,
            key=lambda value: (
                -1 if value[0] is None else value[0],
                "" if value[1] is None else value[1],
            ),
        )

    def count_selected(self) -> int:
        return len(self.list_selected())

    def list_items(self) -> list[dict[str, Any]]:
        return sorted(
            self._cache().get("items", []), key=lambda item: item.get("item_id", 0)
        )

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

    def _find_or_create_item_in_cache(
        self, cache: dict[str, Any], item_id: int, name: str | None
    ) -> dict[str, Any]:
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

        if self.paths.cache_path.exists():
            self._cache_data = read_json(self.paths.cache_path)
            return self._cache_data

        migrated = self._try_migrate_from_sqlite()
        if migrated is not None:
            self._cache_data = migrated
            write_json(self.paths.cache_path, self._cache_data)
            return self._cache_data

        self._cache_data = {"labels": [], "review_labels": [], "items": []}
        self._dirty = True
        return self._cache_data

    def _try_migrate_from_sqlite(self) -> dict[str, Any] | None:
        db_path = self.paths.db_path
        if not db_path.exists():
            return None

        try:
            conn = sqlite3.connect(str(db_path))
        except sqlite3.Error:
            return None

        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='classification_image'"
            ).fetchone()
            if row is None:
                return None
            rows = conn.execute(
                "SELECT name, item_id, selected FROM classification_image ORDER BY item_id"
            ).fetchall()
        except sqlite3.Error:
            return None
        finally:
            conn.close()

        items = [
            {
                "item_id": item_id,
                "name": name,
                "selected": bool(selected),
            }
            for name, item_id, selected in rows
        ]

        return {
            "labels": [],
            "review_labels": [],
            "items": items,
            "migration_version": FILTERING_CACHE_MIGRATION_VERSION,
        }
