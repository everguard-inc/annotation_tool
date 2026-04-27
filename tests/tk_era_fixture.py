"""Factories that write synthetic Tk-era project directories to disk.

Shape matches what Tk `main` leaves on disk for a user who has done some work
on a project. Used as input to Fork B migrator tests.

Schemas copied from `annotation_tool/main` models (verified 2026-04-23 against
`/home/yehor/Work/annotation_tool` models.py and per-mode models.py files).
"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValueRow:
    name: str
    value: str


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))


def _create_value_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS value ("
        "id INTEGER PRIMARY KEY, "
        "name VARCHAR, "
        "value VARCHAR)"
    )


def _insert_values(conn: sqlite3.Connection, rows: list[ValueRow]) -> None:
    conn.executemany(
        "INSERT INTO value (name, value) VALUES (?, ?)",
        [(row.name, row.value) for row in rows],
    )


def _write_state_json(
    project_dir: Path, project_id: int, uid: str, stage: str, mode: str
) -> None:
    payload = {
        "id": project_id,
        "uid": uid,
        "annotation_stage": stage,
        "annotation_mode": mode,
    }
    (project_dir / "state.json").write_text(json.dumps(payload), encoding="utf-8")


DEFAULT_LABELING_LABELS: list[dict] = [
    {"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"},
    {"name": "truck", "color": "blue", "hotkey": "2", "type": "BBOX"},
]

DEFAULT_LABELING_IMAGES: list[dict] = [
    {"name": "a.jpg", "height": 10, "width": 20},
]


def create_tk_era_labeling_project_dir(
    data_dir: Path,
    project_id: int = 42,
    uid: str = "tk-era-labeling",
    item_id: int = 3,
    duration_hours: float = 1.25,
    processed_item_ids: list[int] | None = None,
    labels: list[dict] | None = None,
    images: list[dict] | None = None,
    stage: str = "ANNOTATE",
    mode: str = "OBJECT_DETECTION",
    create_images: bool = False,
) -> Path:
    """Write a project directory that a Tk-era labeling user would leave behind.

    Populates:
      - state.json (ProjectData)
      - db.sqlite with the Tk labeling schema:
        - `value` carrying item_id / duration_hours / processed_item_ids
        - `label` rows (labels + review labels)
        - `image` rows
        - `bbox` / `mask` / `keypoint_group` / `review_label` rows attached to
          each image via `item_id = image.id`

    Each image in `images` may carry inline `bboxes`, `masks`, `kgroups`, and
    `review_labels` lists. See DEFAULT_LABELING_IMAGES for the baseline shape.
    Labels default to DEFAULT_LABELING_LABELS — add entries with type
    `REVIEW_LABEL` to populate the review-labels side of cache.json.
    """
    processed = processed_item_ids if processed_item_ids is not None else [0, 1, 2]
    label_rows = labels if labels is not None else DEFAULT_LABELING_LABELS
    image_rows = images if images is not None else DEFAULT_LABELING_IMAGES

    project_dir = data_dir / "data" / f"{project_id:05d}"
    project_dir.mkdir(parents=True, exist_ok=True)

    if create_images:
        from tests.conftest import create_pattern_image

        images_dir = project_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        for image in image_rows:
            create_pattern_image(
                images_dir / image["name"],
                size=(image["width"], image["height"]),
                base=(240, 240, 240),
            )

    _write_state_json(project_dir, project_id, uid, stage, mode)

    db_path = project_dir / "db.sqlite"
    db_path.unlink(missing_ok=True)
    conn = _connect(db_path)
    try:
        _create_value_table(conn)
        _insert_values(
            conn,
            [
                ValueRow("item_id", str(item_id)),
                ValueRow("duration_hours", str(duration_hours)),
                ValueRow("processed_item_ids", json.dumps(processed)),
            ],
        )

        conn.execute(
            "CREATE TABLE IF NOT EXISTS label ("
            "id INTEGER PRIMARY KEY, "
            "name VARCHAR, "
            "color VARCHAR, "
            "hotkey VARCHAR, "
            "type VARCHAR, "
            "attributes VARCHAR)"
        )
        conn.executemany(
            "INSERT INTO label (name, color, hotkey, type, attributes) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row["name"],
                    row.get("color", "gray"),
                    row.get("hotkey", ""),
                    row.get("type", "BBOX"),
                    row.get("attributes"),
                )
                for row in label_rows
            ],
        )

        conn.execute(
            "CREATE TABLE IF NOT EXISTS image ("
            "id INTEGER PRIMARY KEY, "
            "name VARCHAR UNIQUE, "
            "height INTEGER, "
            "width INTEGER, "
            "trash BOOLEAN, "
            "requires_annotation BOOLEAN)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS bbox ("
            "id INTEGER PRIMARY KEY, "
            "item_id INTEGER, "
            "x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER, "
            "label VARCHAR)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS mask ("
            "id INTEGER PRIMARY KEY, "
            "item_id INTEGER, "
            "rle VARCHAR, "
            "label VARCHAR, "
            "height INTEGER, "
            "width INTEGER)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS keypoint_group ("
            "id INTEGER PRIMARY KEY, "
            "item_id INTEGER, "
            "label VARCHAR, "
            "keypoints_data VARCHAR)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS review_label ("
            "id INTEGER PRIMARY KEY, "
            "item_id INTEGER, "
            "x INTEGER, y INTEGER, "
            "label VARCHAR)"
        )

        for image in image_rows:
            cursor = conn.execute(
                "INSERT INTO image (name, height, width, trash, requires_annotation) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    image["name"],
                    image["height"],
                    image["width"],
                    1 if image.get("trash") else 0,
                    1 if image.get("requires_annotation", True) else 0,
                ),
            )
            image_row_id = cursor.lastrowid

            for bbox in image.get("bboxes", []):
                conn.execute(
                    "INSERT INTO bbox (item_id, x1, y1, x2, y2, label) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        image_row_id,
                        bbox["x1"],
                        bbox["y1"],
                        bbox["x2"],
                        bbox["y2"],
                        bbox["label"],
                    ),
                )

            for mask in image.get("masks", []):
                conn.execute(
                    "INSERT INTO mask (item_id, rle, label, height, width) VALUES (?, ?, ?, ?, ?)",
                    (
                        image_row_id,
                        mask["rle"],
                        mask["label"],
                        mask.get("height", image["height"]),
                        mask.get("width", image["width"]),
                    ),
                )

            for kgroup in image.get("kgroups", []):
                keypoints_data = kgroup.get("keypoints_data")
                if keypoints_data is None and "points" in kgroup:
                    keypoints_data = json.dumps(kgroup["points"])
                conn.execute(
                    "INSERT INTO keypoint_group (item_id, label, keypoints_data) VALUES (?, ?, ?)",
                    (image_row_id, kgroup["label"], keypoints_data),
                )

            for review_label in image.get("review_labels", []):
                conn.execute(
                    "INSERT INTO review_label (item_id, x, y, label) VALUES (?, ?, ?, ?)",
                    (
                        image_row_id,
                        review_label["x"],
                        review_label["y"],
                        review_label["label"],
                    ),
                )

        conn.commit()
    finally:
        conn.close()

    return project_dir


def create_tk_era_filtering_project_dir(
    data_dir: Path,
    project_id: int = 43,
    uid: str = "tk-era-filtering",
    item_id: int = 2,
    duration_hours: float = 0.5,
    processed_item_ids: list[int] | None = None,
    selected_items: list[tuple[int, str]] | None = None,
    total_items: int = 5,
) -> Path:
    """Write a project directory that a Tk-era filtering user would leave behind.

    Populates:
      - state.json (ProjectData, mode=FILTERING)
      - db.sqlite with a `value` table and a `classification_image` table.

    `selected_items` entries supply both the item_id and the name for those
    rows; unlisted item_ids default to `frame_{fid}.jpg`. Set `total_items`
    to control how many classification_image rows are written.
    """
    processed = processed_item_ids if processed_item_ids is not None else [0, 1]
    selected = (
        selected_items
        if selected_items is not None
        else [(0, "frame_0.jpg"), (2, "frame_2.jpg")]
    )

    project_dir = data_dir / "data" / f"{project_id:05d}"
    project_dir.mkdir(parents=True, exist_ok=True)

    _write_state_json(project_dir, project_id, uid, "FILTERING", "FILTERING")

    db_path = project_dir / "db.sqlite"
    db_path.unlink(missing_ok=True)
    conn = _connect(db_path)
    try:
        _create_value_table(conn)
        _insert_values(
            conn,
            [
                ValueRow("item_id", str(item_id)),
                ValueRow("duration_hours", str(duration_hours)),
                ValueRow("processed_item_ids", json.dumps(processed)),
            ],
        )

        conn.execute(
            "CREATE TABLE IF NOT EXISTS classification_image ("
            "id INTEGER PRIMARY KEY, "
            "name VARCHAR UNIQUE, "
            "item_id INTEGER, "
            "selected BOOLEAN)"
        )
        name_by_id = {item_id: name for item_id, name in selected}
        rows = []
        for fid in range(total_items):
            name = name_by_id.get(fid, f"frame_{fid}.jpg")
            rows.append((name, fid, 1 if fid in name_by_id else 0))
        conn.executemany(
            "INSERT INTO classification_image (name, item_id, selected) VALUES (?, ?, ?)",
            rows,
        )

        conn.commit()
    finally:
        conn.close()

    return project_dir
