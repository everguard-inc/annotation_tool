import json
from pathlib import Path

from annotation_tool.core.paths import FilteringPaths, LabelingPaths
from annotation_tool.services.session_state import (
    SESSION_STATE_MIGRATION_VERSION,
    SessionState,
    SessionStateStore,
)
from tests.tk_era_fixture import (
    create_tk_era_filtering_project_dir,
    create_tk_era_labeling_project_dir,
)


def test_session_state_store_seeds_runtime_state_from_tk_labeling_db(
    data_dir: Path,
) -> None:
    """Covers ADR-backed roadmap step 1: labeling project upgraded from Tk main
    must surface its last item_id, duration, and processed-item set on first
    PySide open instead of starting fresh."""
    create_tk_era_labeling_project_dir(
        data_dir,
        project_id=42,
        item_id=3,
        duration_hours=1.25,
        processed_item_ids=[0, 1, 2],
    )

    paths = LabelingPaths(data_dir, 42)
    assert not paths.runtime_state_path.exists()

    store = SessionStateStore(paths.runtime_state_path, migration_db_path=paths.db_path)
    state = store.load()

    assert state.item_id == 3
    assert state.duration_hours == 1.25
    assert state.processed_item_ids == {0, 1, 2}

    assert paths.runtime_state_path.exists()
    persisted = json.loads(paths.runtime_state_path.read_text(encoding="utf-8"))
    assert persisted["item_id"] == 3
    assert persisted["duration_hours"] == 1.25
    assert persisted["processed_item_ids"] == [0, 1, 2]
    assert persisted["migration_version"] == SESSION_STATE_MIGRATION_VERSION


def test_session_state_store_seeds_runtime_state_from_tk_filtering_db(
    data_dir: Path,
) -> None:
    """Filtering-mode upgrade path from Tk main."""
    create_tk_era_filtering_project_dir(
        data_dir,
        project_id=43,
        item_id=2,
        duration_hours=0.5,
        processed_item_ids=[0, 1],
    )

    paths = FilteringPaths(data_dir, 43)
    store = SessionStateStore(paths.runtime_state_path, migration_db_path=paths.db_path)

    state = store.load()

    assert state.item_id == 2
    assert state.duration_hours == 0.5
    assert state.processed_item_ids == {0, 1}


def test_session_state_store_migration_is_idempotent(data_dir: Path) -> None:
    """Subsequent loads must read the seeded JSON and ignore the SQLite source."""
    create_tk_era_labeling_project_dir(
        data_dir,
        project_id=44,
        item_id=5,
        duration_hours=2.0,
        processed_item_ids=[0, 1, 4],
    )
    paths = LabelingPaths(data_dir, 44)
    store = SessionStateStore(paths.runtime_state_path, migration_db_path=paths.db_path)

    store.load()

    store.save(
        SessionState(item_id=7, duration_hours=3.0, processed_item_ids={0, 1, 4, 6})
    )

    replayed = store.load()

    assert replayed.item_id == 7
    assert replayed.duration_hours == 3.0
    assert replayed.processed_item_ids == {0, 1, 4, 6}


def test_session_state_store_defaults_when_neither_json_nor_db_present(
    data_dir: Path,
) -> None:
    paths = LabelingPaths(data_dir, 45)
    paths.ensure_project_dir()

    store = SessionStateStore(paths.runtime_state_path, migration_db_path=paths.db_path)
    state = store.load()

    assert state.item_id == 0
    assert state.duration_hours == 0.0
    assert state.processed_item_ids == set()
    assert not paths.runtime_state_path.exists()


def test_session_state_store_defaults_when_db_has_no_value_table(
    data_dir: Path,
) -> None:
    """Database exists but lacks a value table — migrator must fall back to defaults."""
    import sqlite3

    paths = LabelingPaths(data_dir, 46)
    paths.ensure_project_dir()
    conn = sqlite3.connect(str(paths.db_path))
    conn.execute("CREATE TABLE unrelated (x INTEGER)")
    conn.commit()
    conn.close()

    store = SessionStateStore(paths.runtime_state_path, migration_db_path=paths.db_path)
    state = store.load()

    assert state.item_id == 0
    assert state.duration_hours == 0.0
    assert state.processed_item_ids == set()
