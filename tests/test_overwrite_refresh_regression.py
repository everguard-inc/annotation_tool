"""Regression coverage for the refresh-after-overwrite path.

Drives a real LabelingScreen + LabelingSession + LabelingRepository to
prove that reloading the current item after an overwrite does not
persist the session's stale in-memory controller state back over the
freshly-downloaded cache.json.

The original bug (reported in code review): MainWindow called
current_screen.go_to_id(current_item_id), which routed through
LabelingSession.go_to_item → save_current_item → load_current_item,
so the overwrite was undone by a save before the reload.
"""

import json
from pathlib import Path

from annotation_tool.core.utils import write_json
from annotation_tool.infrastructure.repositories.labeling_repository import (
    LabelingRepository,
)
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.ui.screens.labeling_screen import LabelingScreen


def _simulate_download_overwrite(paths, new_bbox: dict) -> None:
    """Stand-in for ImportExportService.overwrite_annotations: rewrites the
    cache.json that the repository reads so the session sees fresh data on
    the next load_current_item call."""
    data = json.loads(paths.cache_path.read_text(encoding="utf-8"))
    data["figures"]["a.jpg"]["bboxes"] = [new_bbox]
    write_json(paths.cache_path, data)


def _simulate_download_overwrite_with_labels(
    paths, new_bbox: dict, new_labels: list[dict]
) -> None:
    """Same as _simulate_download_overwrite, but also rewrites the label
    catalogue. Mirrors what ImportExportService.overwrite_annotations does
    when the backend ships a different label set."""
    data = json.loads(paths.cache_path.read_text(encoding="utf-8"))
    data["figures"]["a.jpg"]["bboxes"] = [new_bbox]
    data["labels"] = new_labels
    write_json(paths.cache_path, data)


def test_reload_current_annotations_picks_up_overwritten_cache_without_stale_save(
    qapp, data_dir: Path, labeling_project, labeling_cache
) -> None:
    """Covers FR-069. The original local cache carries bbox (2,2,8,7); after
    an overwrite rewrites it to (9,9,18,9), the refresh path must reload
    the new bbox without first writing the stale in-memory controller
    state back to disk."""
    repository = LabelingRepository(data_dir, labeling_project.id)
    session = LabelingSession(labeling_project, repository)
    screen = LabelingScreen(session)

    assert session.image_names[0] == "a.jpg"
    initial_bboxes = [type(figure).__name__ for figure in session.controller.figures()]
    assert initial_bboxes == ["BBox"]

    new_bbox = {"x1": 9, "y1": 9, "x2": 18, "y2": 9, "label": "car"}
    _simulate_download_overwrite(labeling_cache, new_bbox)

    screen.reload_current_annotations()

    reloaded = session.controller.figures()
    assert len(reloaded) == 1
    assert (reloaded[0].x1, reloaded[0].y1, reloaded[0].x2, reloaded[0].y2) == (
        9,
        9,
        18,
        9,
    )

    persisted = json.loads(labeling_cache.cache_path.read_text(encoding="utf-8"))
    assert persisted["figures"]["a.jpg"]["bboxes"] == [new_bbox]


def test_reload_current_annotations_refreshes_label_catalogue_after_overwrite(
    qapp, data_dir: Path, labeling_project, labeling_cache
) -> None:
    """Covers the label-catalogue half of FR-069. If the backend overwrite
    ships a different label set, reload_current_annotations must pick up
    the new labels; otherwise the UI keeps the old chips and active
    label, and newly-committed figures can reference labels that are no
    longer in the catalogue."""
    repository = LabelingRepository(data_dir, labeling_project.id)
    session = LabelingSession(labeling_project, repository)
    screen = LabelingScreen(session)

    initial_names = {label.name for label in session.figure_labels}
    assert initial_names == {"truck", "car", "blur"}

    new_labels = [
        {"name": "pedestrian", "color": "blue", "hotkey": "1", "type": "BBOX"},
        {"name": "cyclist", "color": "red", "hotkey": "2", "type": "BBOX"},
    ]
    new_bbox = {"x1": 9, "y1": 9, "x2": 18, "y2": 9, "label": "pedestrian"}
    _simulate_download_overwrite_with_labels(labeling_cache, new_bbox, new_labels)

    screen.reload_current_annotations()

    refreshed_names = {label.name for label in session.figure_labels}
    assert refreshed_names == {"pedestrian", "cyclist"}
    assert session.active_label is not None
    assert session.active_label.name in refreshed_names
