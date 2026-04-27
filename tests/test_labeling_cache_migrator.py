import json
import sqlite3
from pathlib import Path

from annotation_tool.core.enums import FigureType
from annotation_tool.core.paths import LabelingPaths
from annotation_tool.infrastructure.repositories.labeling_repository import (
    LABELING_CACHE_MIGRATION_VERSION,
    LabelingRepository,
)
from tests.tk_era_fixture import create_tk_era_labeling_project_dir


def test_labeling_repository_migrates_full_annotations_from_tk_db(
    data_dir: Path,
) -> None:
    """Covers ADR-backed roadmap step 1 and the mapping in
    docs/quality/labeling-figure-shape-drill-2026-04-23.md: labels, images,
    bboxes, masks, keypoint groups, and review labels from Tk main must
    surface in cache.json on first PySide open."""
    create_tk_era_labeling_project_dir(
        data_dir,
        project_id=100,
        labels=[
            {"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"},
            {"name": "road", "color": "gray", "hotkey": "3", "type": "MASK"},
            {
                "name": "person",
                "color": "green",
                "hotkey": "4",
                "type": "KGROUP",
                "attributes": '{"ordered": true}',
            },
            {"name": "Fix", "color": "yellow", "hotkey": "1", "type": "REVIEW_LABEL"},
        ],
        images=[
            {
                "name": "a.jpg",
                "height": 10,
                "width": 20,
                "bboxes": [
                    {"x1": 2, "y1": 2, "x2": 8, "y2": 7, "label": "car"},
                ],
                "masks": [
                    {"rle": "RLE_ROAD", "label": "road"},
                ],
                "kgroups": [
                    {
                        "label": "person",
                        "points": [
                            {"x": 1, "y": 2, "label": "head"},
                            {"x": 3, "y": 4, "label": "torso"},
                        ],
                    },
                ],
                "review_labels": [
                    {"x": 5, "y": 5, "label": "Fix"},
                ],
            },
            {"name": "b.jpg", "height": 10, "width": 20, "trash": True},
        ],
    )

    paths = LabelingPaths(data_dir, 100)
    assert not paths.cache_path.exists()

    repository = LabelingRepository(data_dir, 100)
    figure_labels = repository.get_figure_labels()
    review_labels = repository.get_review_labels()
    image_names = repository.list_image_names()

    assert {label.name for label in figure_labels} == {"car", "road", "person"}
    assert {label.name for label in review_labels} == {"Fix"}
    assert image_names == ["a.jpg", "b.jpg"]

    person = next(label for label in figure_labels if label.name == "person")
    assert person.type is FigureType.KGROUP
    assert person.attributes == '{"ordered": true}'

    a_ann = repository.load_image_annotations("a.jpg")
    assert a_ann["figures"]["bboxes"] == [
        {"x1": 2, "y1": 2, "x2": 8, "y2": 7, "label": "car"}
    ]
    assert a_ann["figures"]["masks"] == {"road": "RLE_ROAD"}
    assert a_ann["figures"]["kgroups"] == [
        {
            "label": "person",
            "points": [
                {"x": 1, "y": 2, "label": "head"},
                {"x": 3, "y": 4, "label": "torso"},
            ],
        }
    ]
    assert a_ann["figures"]["trash"] is False
    assert a_ann["review"] == [{"x": 5, "y": 5, "label": "Fix"}]

    b_ann = repository.load_image_annotations("b.jpg")
    assert b_ann["figures"]["trash"] is True
    assert b_ann["figures"]["bboxes"] == []
    assert b_ann["figures"]["kgroups"] == []
    assert b_ann["figures"]["masks"] == {}
    assert b_ann["review"] == []

    persisted = json.loads(paths.cache_path.read_text(encoding="utf-8"))
    assert persisted["migration_version"] == LABELING_CACHE_MIGRATION_VERSION


def test_labeling_repository_ignores_sqlite_when_cache_json_already_exists(
    data_dir: Path,
) -> None:
    """Once cache.json exists, the migrator must not run."""
    create_tk_era_labeling_project_dir(
        data_dir,
        project_id=101,
        images=[
            {
                "name": "x.jpg",
                "height": 10,
                "width": 20,
                "bboxes": [{"x1": 0, "y1": 0, "x2": 5, "y2": 5, "label": "car"}],
            }
        ],
    )

    paths = LabelingPaths(data_dir, 101)
    paths.cache_path.write_text(
        json.dumps(
            {
                "labels": [],
                "review_labels": [],
                "items": [
                    {
                        "name": "pyside.jpg",
                        "height": 1,
                        "width": 1,
                        "requires_annotation": True,
                    }
                ],
                "figures": {
                    "pyside.jpg": {
                        "trash": False,
                        "bboxes": [],
                        "kgroups": [],
                        "masks": {},
                        "height": 1,
                        "width": 1,
                    }
                },
                "review": {},
            }
        ),
        encoding="utf-8",
    )

    repository = LabelingRepository(data_dir, 101)
    assert repository.list_image_names() == ["pyside.jpg"]


def test_labeling_repository_skips_kgroup_with_malformed_keypoints_data(
    data_dir: Path,
) -> None:
    """Drill edge case: malformed keypoints_data must be skipped without
    crashing the migration."""
    create_tk_era_labeling_project_dir(
        data_dir,
        project_id=102,
        labels=[{"name": "person", "color": "green", "hotkey": "1", "type": "KGROUP"}],
        images=[{"name": "a.jpg", "height": 10, "width": 20}],
    )
    paths = LabelingPaths(data_dir, 102)

    conn = sqlite3.connect(str(paths.db_path))
    try:
        conn.execute(
            "INSERT INTO keypoint_group (item_id, label, keypoints_data) VALUES (?, ?, ?)",
            (1, "person", "not-json"),
        )
        conn.commit()
    finally:
        conn.close()

    repository = LabelingRepository(data_dir, 102)
    ann = repository.load_image_annotations("a.jpg")
    assert ann["figures"]["kgroups"] == []


def test_labeling_repository_skips_figures_with_dangling_item_fk(
    data_dir: Path,
) -> None:
    """Drill edge case: bbox/mask/kgroup/review rows that reference a
    non-existent image row must be ignored rather than attached."""
    create_tk_era_labeling_project_dir(
        data_dir,
        project_id=103,
        images=[{"name": "a.jpg", "height": 10, "width": 20}],
    )
    paths = LabelingPaths(data_dir, 103)

    conn = sqlite3.connect(str(paths.db_path))
    try:
        conn.execute(
            "INSERT INTO bbox (item_id, x1, y1, x2, y2, label) VALUES (?, ?, ?, ?, ?, ?)",
            (9999, 0, 0, 1, 1, "car"),
        )
        conn.execute(
            "INSERT INTO review_label (item_id, x, y, label) VALUES (?, ?, ?, ?)",
            (9999, 0, 0, "Fix"),
        )
        conn.commit()
    finally:
        conn.close()

    repository = LabelingRepository(data_dir, 103)
    assert repository.load_image_annotations("a.jpg")["figures"]["bboxes"] == []
    assert repository.load_image_annotations("a.jpg")["review"] == []


def test_labeling_repository_falls_back_to_empty_when_no_sources(
    data_dir: Path,
) -> None:
    paths = LabelingPaths(data_dir, 104)
    paths.ensure_project_dir()

    repository = LabelingRepository(data_dir, 104)
    assert repository.list_image_names() == []
    assert repository.get_figure_labels() == []
