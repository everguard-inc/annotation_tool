from dataclasses import dataclass


@dataclass
class SessionState:
    item_id: int
    duration_hours: float
    processed_item_ids: set[int]


class SessionStateStore:
    def load(self) -> SessionState:
        ...

    def save(self, state: SessionState) -> None:
        ...

    def reset(self) -> None:
        ...
