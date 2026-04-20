from pathlib import Path
from sqlalchemy.orm import Session


class Database:
    def __init__(self) -> None:
        ...

    def configure(self, db_path: Path) -> None:
        ...

    def session(self) -> Session:
        ...

    def close(self) -> None:
        ...
