from pathlib import Path

from annotation_tool.core.enums import AnnotationStage
from annotation_tool.services.session_state import SessionState, SessionStateStore
from annotation_tool.services.statistics_service import StatisticsService


def test_runtime_state_and_statistics_are_persisted(tmp_path: Path, monkeypatch) -> None:
    """Covers FR-037, FR-038, FR-039, FR-040, FR-041, FR-191, FR-192."""
    state_path = tmp_path / "runtime_state.json"
    statistics_path = tmp_path / "statistics.txt"

    store = SessionStateStore(state_path)
    store.save(SessionState(item_id=5, duration_hours=1.25, processed_item_ids={1, 2, 5}))

    loaded = store.load()

    assert loaded.item_id == 5
    assert loaded.duration_hours == 1.25
    assert loaded.processed_item_ids == {1, 2, 5}

    timestamps = iter([100.0, 103.0])
    monkeypatch.setattr("annotation_tool.services.statistics_service.time.time", lambda: next(timestamps))

    statistics = StatisticsService(statistics_path)
    duration = statistics.track_action(AnnotationStage.ANNOTATE, "keyboard")

    assert duration == 3 / 3600
    assert "ANNOTATE" in statistics_path.read_text(encoding="utf-8")
    assert "keyboard" in statistics_path.read_text(encoding="utf-8")
