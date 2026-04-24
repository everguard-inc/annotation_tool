import json
import sqlite3
from pathlib import Path

from annotation_tool.core.paths import EventValidationPaths
from annotation_tool.infrastructure.repositories.event_validation_repository import (
    EventValidationRepository,
)


def test_event_validation_repository_migrates_tk_sqlite_cache(
    data_dir: Path,
) -> None:
    """Pins origin/main Tk schema:
    annotation_widgets/event_validation/models.py defines event.id,
    event.uid, event.comment, and event.custom_fields.
    models.Value supplies value.name/value.value for the fields payload.
    """
    paths = EventValidationPaths(data_dir, 42)
    paths.ensure_project_dir()
    conn = sqlite3.connect(paths.db_path)
    conn.execute("CREATE TABLE value (id INTEGER PRIMARY KEY, name TEXT, value TEXT)")
    conn.execute(
        "INSERT INTO value (name, value) VALUES (?, ?)",
        (
            "fields",
            json.dumps({"Status": {"TP": "green", "FP": "red"}}),
        ),
    )
    conn.execute(
        "CREATE TABLE event (id INTEGER PRIMARY KEY, uid TEXT, comment TEXT, custom_fields TEXT)"
    )
    conn.execute(
        "INSERT INTO event (uid, comment, custom_fields) VALUES (?, ?, ?)",
        ("ev-a", "checked", json.dumps(["TP"])),
    )
    conn.commit()
    conn.close()

    repository = EventValidationRepository(data_dir, 42)

    assert repository.fields() == {"Status": {"TP": "green", "FP": "red"}}
    assert repository.events()[0]["uid"] == "ev-a"
    assert repository.events()[0]["comment"] == "checked"
    assert repository.events()[0]["answers"] == ["TP"]
    assert paths.cache_path.exists()


def test_event_validation_repository_counts_incomplete_events(data_dir: Path) -> None:
    paths = EventValidationPaths(data_dir, 43)
    paths.ensure_project_dir()
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {
                    "ev-a": {"answers": ["TP"], "comment": ""},
                    "ev-b": {"answers": [""], "comment": ""},
                    "ev-c": {"answers": [], "comment": ""},
                },
            }
        ),
        encoding="utf-8",
    )

    repository = EventValidationRepository(data_dir, 43)

    assert repository.count_incomplete() == 2
