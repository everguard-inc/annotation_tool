import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from annotation_tool.core.utils import read_json, write_json

SESSION_STATE_MIGRATION_VERSION = 1


@dataclass
class SessionState:
    item_id: int
    duration_hours: float
    processed_item_ids: set[int]


class SessionStateStore:
    def __init__(self, path: Path, migration_db_path: Path | None = None) -> None:
        self.path = path
        self.migration_db_path = migration_db_path

    def load(self) -> SessionState:
        if self.path.exists():
            data = read_json(self.path)
            return SessionState(
                item_id=int(data.get("item_id", 0)),
                duration_hours=float(data.get("duration_hours", 0.0)),
                processed_item_ids={
                    int(item_id) for item_id in data.get("processed_item_ids", [])
                },
            )

        migrated = self._try_migrate_from_sqlite()
        if migrated is not None:
            self.save(migrated)
            return migrated

        return SessionState(item_id=0, duration_hours=0.0, processed_item_ids=set())

    def save(self, state: SessionState) -> None:
        write_json(
            self.path,
            {
                "item_id": state.item_id,
                "duration_hours": state.duration_hours,
                "processed_item_ids": sorted(state.processed_item_ids),
                "migration_version": SESSION_STATE_MIGRATION_VERSION,
            },
        )

    def reset(self) -> None:
        self.save(SessionState(item_id=0, duration_hours=0.0, processed_item_ids=set()))

    def _try_migrate_from_sqlite(self) -> SessionState | None:
        if self.migration_db_path is None or not self.migration_db_path.exists():
            return None

        try:
            conn = sqlite3.connect(str(self.migration_db_path))
        except sqlite3.Error:
            return None

        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='value'"
            ).fetchone()
            if row is None:
                return None

            values = dict(conn.execute("SELECT name, value FROM value").fetchall())
        except sqlite3.Error:
            return None
        finally:
            conn.close()

        if not values:
            return None

        return SessionState(
            item_id=int(values.get("item_id", 0)),
            duration_hours=float(values.get("duration_hours", 0.0)),
            processed_item_ids=set(json.loads(values.get("processed_item_ids", "[]"))),
        )
