"""Regression tests for Fork B's session-state persistence path.

These exercise ``_persist_session_state`` on both session classes via real
navigation calls so an unused-import pruning (e.g. formatter stripping
``SessionState``) is caught as a test failure rather than a production
crash on the first save boundary.
"""

import json
from pathlib import Path

import numpy as np

from annotation_tool.core.paths import FilteringPaths, LabelingPaths
from annotation_tool.infrastructure.repositories.filtering_repository import (
    FilteringRepository,
)
from annotation_tool.infrastructure.repositories.labeling_repository import (
    LabelingRepository,
)
from annotation_tool.services.filtering_session import FilteringSession
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.services.session_state import SessionStateStore


class FakeFrameProvider:
    def __init__(self) -> None:
        self.prefetched: list[tuple[int, int]] = []

    def open(self) -> None:
        pass

    def frame_count(self) -> int:
        return 5

    def request_frame(self, index: int):
        return np.full((10, 10, 3), index, dtype=np.uint8)

    def prefetch(self, start_index: int, direction: int) -> None:
        self.prefetched.append((start_index, direction))

    def close(self) -> None:
        pass


class NameOnlyDecoder:
    def decode_image_name(self, frame) -> str:
        return f"frame_{int(frame[0, 0, 0])}.jpg"


def test_filtering_session_persists_item_id_and_processed_items(
    data_dir: Path, filtering_project, filtering_paths
) -> None:
    store = SessionStateStore(filtering_paths.runtime_state_path)
    session = FilteringSession(
        FakeFrameProvider(),
        FilteringRepository(data_dir, filtering_project.id),
        NameOnlyDecoder(),
        session_state_store=store,
    )

    session.next_item()
    session.next_item()

    persisted = json.loads(
        filtering_paths.runtime_state_path.read_text(encoding="utf-8")
    )
    assert persisted["item_id"] == 2
    assert persisted["processed_item_ids"] == [0, 1]


def test_labeling_session_persists_item_id_on_navigation(
    data_dir: Path, labeling_project, labeling_cache
) -> None:
    paths = LabelingPaths(data_dir, labeling_project.id)
    store = SessionStateStore(paths.runtime_state_path)

    session = LabelingSession(
        labeling_project,
        LabelingRepository(data_dir, labeling_project.id),
        session_state_store=store,
    )

    assert session.item_count() >= 2
    session.next_item()

    persisted = json.loads(paths.runtime_state_path.read_text(encoding="utf-8"))
    assert persisted["item_id"] == 1
    assert persisted["processed_item_ids"] == [0]


def test_filtering_session_seeds_item_id_from_store_on_open(
    data_dir: Path, filtering_project, filtering_paths
) -> None:
    paths = FilteringPaths(data_dir, filtering_project.id)
    paths.runtime_state_path.write_text(
        json.dumps(
            {
                "item_id": 3,
                "duration_hours": 0.75,
                "processed_item_ids": [0, 1, 2],
                "migration_version": 1,
            }
        ),
        encoding="utf-8",
    )

    session = FilteringSession(
        FakeFrameProvider(),
        FilteringRepository(data_dir, filtering_project.id),
        NameOnlyDecoder(),
        session_state_store=SessionStateStore(paths.runtime_state_path),
    )

    assert session.current_item_id() == 3
    assert session.duration_hours == 0.75
    assert session.processed_item_ids == {0, 1, 2}


class FakeStatistics:
    def __init__(self) -> None:
        self.calls = []
        self.duration_hours = 0.0

    def track_action(self, stage, message=None):
        self.calls.append((stage, message))
        self.duration_hours = 1.25
        return self.duration_hours


def test_labeling_actions_update_duration_and_statistics(
    data_dir: Path, labeling_project, labeling_cache
) -> None:
    repository = LabelingRepository(data_dir, labeling_project.id)
    session = LabelingSession(labeling_project, repository)
    statistics = FakeStatistics()
    session.statistics_service = statistics

    session.handle_mouse_press(2, 2)

    assert session.duration_hours == 1.25
    assert statistics.calls == [(labeling_project.stage, "lmp")]


def test_filtering_actions_update_duration_and_statistics(
    data_dir: Path,
    filtering_project,
    filtering_paths,
) -> None:
    repository = FilteringRepository(data_dir, filtering_project.id)
    session = FilteringSession(FakeFrameProvider(), repository, NameOnlyDecoder())
    statistics = FakeStatistics()
    session.statistics_service = statistics

    session.toggle_selected()

    assert session.duration_hours == 1.25
    assert statistics.calls == [(filtering_project.stage, "keyboard")]
