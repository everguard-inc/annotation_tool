from dataclasses import dataclass
from pathlib import Path

from annotation_tool.core.utils import read_json, write_json


@dataclass
class SessionState:
    item_id: int
    duration_hours: float
    processed_item_ids: set[int]


class SessionStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> SessionState:
        if not self.path.exists():
            return SessionState(item_id=0, duration_hours=0.0, processed_item_ids=set())

        data = read_json(self.path)
        return SessionState(
            item_id=int(data.get("item_id", 0)),
            duration_hours=float(data.get("duration_hours", 0.0)),
            processed_item_ids={int(item_id) for item_id in data.get("processed_item_ids", [])},
        )

    def save(self, state: SessionState) -> None:
        write_json(
            self.path,
            {
                "item_id": state.item_id,
                "duration_hours": state.duration_hours,
                "processed_item_ids": sorted(state.processed_item_ids),
            },
        )

    def reset(self) -> None:
        self.save(SessionState(item_id=0, duration_hours=0.0, processed_item_ids=set()))
