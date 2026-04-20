from typing import Any


class ValueRepository:
    def get(self, name: str) -> str | None:
        ...

    def set(self, name: str, value: Any, overwrite: bool = True) -> None:
        ...

    def reset_session_values(self) -> None:
        ...
