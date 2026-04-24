from pathlib import Path

import numpy as np

from annotation_tool.core.utils import read_json, write_json
from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession


def test_render_modes_change_output_and_persist_trash_flag(data_dir: Path, labeling_project, labeling_cache) -> None:
    """Covers FR-085, FR-086, FR-087, FR-088, FR-118, FR-119, FR-120, FR-121, FR-186, FR-187, FR-188, FR-189, FR-190."""
    repository = LabelingRepository(data_dir, labeling_project.id)
    session = LabelingSession(labeling_project, repository)

    session.go_to_item(0)
    normal_frame = session.render_frame()

    session.toggle_figures_visibility()
    hidden_frame = session.render_frame()

    session.toggle_degraded_preview()
    degraded_frame = session.render_frame()

    assert not np.array_equal(normal_frame, hidden_frame)
    assert not np.array_equal(hidden_frame, degraded_frame)
    assert session.editing_blocked() is True

    session.toggle_trash()
    assert session.status().is_trash is True


def test_blur_label_blurs_image_region(data_dir, labeling_project, labeling_cache) -> None:
    cache = read_json(labeling_cache.cache_path)
    cache["figures"]["a.jpg"]["bboxes"] = [
        {"x1": 0, "y1": 0, "x2": 12, "y2": 9, "label": "blur"}
    ]
    write_json(labeling_cache.cache_path, cache)

    repository = LabelingRepository(data_dir, labeling_project.id)
    session = LabelingSession(labeling_project, repository)

    rendered = session.render_frame()
    session.toggle_figures_visibility()
    without_figures = session.render_frame()

    assert (rendered[5, 5] != without_figures[5, 5]).any()
