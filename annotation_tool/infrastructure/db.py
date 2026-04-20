from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


class Database:
    def __init__(self) -> None:
        self._engine = None
        self._session_factory: sessionmaker | None = None

    def configure(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_engine(f"sqlite:///{db_path}?check_same_thread=False")

        with self._engine.connect() as connection:
            connection.execute(text("PRAGMA synchronous = NORMAL"))
            connection.execute(text("PRAGMA journal_mode = WAL"))

        self._session_factory = sessionmaker(bind=self._engine)

    def session(self) -> Session:
        if self._session_factory is None:
            raise RuntimeError("Database is not configured.")
        return self._session_factory()

    def close(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
