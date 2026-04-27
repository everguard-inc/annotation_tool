import json
from pathlib import Path

from annotation_tool.core.paths import FilteringPaths
from annotation_tool.infrastructure.repositories.filtering_repository import (
    FILTERING_CACHE_MIGRATION_VERSION,
    FilteringRepository,
)
from tests.tk_era_fixture import create_tk_era_filtering_project_dir


def test_filtering_repository_migrates_selections_from_tk_db(data_dir: Path) -> None:
    """Covers ADR-backed roadmap step 1: filtering selections from Tk main
    classification_image rows must surface on first PySide open via
    cache.json bootstrap. Uses non-default names to prove the migrator
    preserves legacy classification_image.name values verbatim rather
    than recomputing them from item_id."""
    create_tk_era_filtering_project_dir(
        data_dir,
        project_id=50,
        selected_items=[(0, "legacy_a.jpg"), (2, "legacy_b.jpg")],
    )

    paths = FilteringPaths(data_dir, 50)
    assert not paths.cache_path.exists()

    repository = FilteringRepository(data_dir, 50)
    selected = repository.list_selected()

    assert selected == [(0, "legacy_a.jpg"), (2, "legacy_b.jpg")]

    assert paths.cache_path.exists()
    persisted = json.loads(paths.cache_path.read_text(encoding="utf-8"))
    assert persisted["migration_version"] == FILTERING_CACHE_MIGRATION_VERSION
    assert len(persisted["items"]) == 5  # fixture generates 5 frames by default
    selected_entries = [item for item in persisted["items"] if item["selected"]]
    assert {(item["item_id"], item["name"]) for item in selected_entries} == {
        (0, "legacy_a.jpg"),
        (2, "legacy_b.jpg"),
    }


def test_filtering_repository_ignores_sqlite_when_cache_json_already_exists(
    data_dir: Path,
) -> None:
    """Once cache.json exists, it wins — SQLite is ignored even if populated."""
    create_tk_era_filtering_project_dir(
        data_dir, project_id=51, selected_items=[(0, "frame_0.jpg")]
    )

    paths = FilteringPaths(data_dir, 51)
    paths.cache_path.write_text(
        json.dumps(
            {
                "labels": [],
                "review_labels": [],
                "items": [
                    {"item_id": 4, "name": "frame_4.jpg", "selected": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    repository = FilteringRepository(data_dir, 51)
    selected = repository.list_selected()

    assert selected == [(4, "frame_4.jpg")]


def test_filtering_repository_falls_back_to_empty_when_no_sources(
    data_dir: Path,
) -> None:
    paths = FilteringPaths(data_dir, 52)
    paths.ensure_project_dir()

    repository = FilteringRepository(data_dir, 52)
    assert repository.list_selected() == []
