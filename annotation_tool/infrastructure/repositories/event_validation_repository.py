import json
import sqlite3
from pathlib import Path
from typing import Any

from annotation_tool.core.paths import EventValidationPaths
from annotation_tool.core.utils import read_json, write_json


class EventValidationRepository:
    def __init__(self, data_dir: Path, project_id: int) -> None:
        self.paths = EventValidationPaths(data_dir, project_id)

    def fields(self) -> dict[str, dict[str, str]]:
        return dict(self._cache().get("fields", {}))

    def events(self) -> list[dict[str, Any]]:
        events = self._cache().get("events", {})
        return [
            {"uid": uid, **dict(data)}
            for uid, data in sorted(events.items(), key=lambda item: item[0])
        ]

    def event(self, uid: str) -> dict[str, Any]:
        data = self._cache().get("events", {}).get(uid, {})
        return {
            "uid": uid,
            "answers": list(data.get("answers", [])),
            "comment": data.get("comment") or "",
        }

    def save_event(self, uid: str, answers: list[str], comment: str) -> None:
        cache = self._cache()
        cache.setdefault("events", {})[uid] = {
            "answers": list(answers),
            "comment": comment,
        }
        write_json(self.paths.cache_path, cache)

    def count_incomplete(self) -> int:
        count = 0
        for event in self.events():
            answers = event.get("answers", [])
            if not answers or any(str(answer).strip() == "" for answer in answers):
                count += 1
        return count

    def _cache(self) -> dict[str, Any]:
        if self.paths.cache_path.exists():
            return read_json(self.paths.cache_path)

        migrated = self._try_migrate_from_sqlite()
        if migrated is not None:
            write_json(self.paths.cache_path, migrated)
            return migrated

        return {"fields": {}, "events": {}}

    def _try_migrate_from_sqlite(self) -> dict[str, Any] | None:
        if not self.paths.db_path.exists():
            return None

        try:
            conn = sqlite3.connect(str(self.paths.db_path))
        except sqlite3.Error:
            return None

        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "event" not in tables:
                return None

            fields = {}
            if "value" in tables:
                row = conn.execute(
                    "SELECT value FROM value WHERE name='fields'"
                ).fetchone()
                fields = json.loads(row[0]) if row and row[0] else {}

            rows = conn.execute(
                "SELECT uid, comment, custom_fields FROM event ORDER BY uid"
            ).fetchall()
        except (sqlite3.Error, json.JSONDecodeError):
            return None
        finally:
            conn.close()

        return {
            "fields": fields,
            "events": {
                uid: {
                    "answers": json.loads(custom_fields) if custom_fields else [],
                    "comment": comment or "",
                }
                for uid, comment, custom_fields in rows
            },
        }
