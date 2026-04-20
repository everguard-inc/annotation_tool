from pathlib import Path

from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.ui.screens.labeling_screen import LabelingScreen


def test_keyboard_and_mouse_events_update_session_state(qapp, data_dir: Path, labeling_project, labeling_cache, monkeypatch) -> None:
    """Covers FR-128, FR-129, FR-130, FR-131, FR-132, FR-133, FR-134, FR-135, FR-136, FR-137, FR-138, FR-143, FR-147, FR-193."""
    repository = LabelingRepository(data_dir, labeling_project.id)
    session = LabelingSession(labeling_project, repository)
    screen = LabelingScreen(session)

    monkeypatch.setattr("annotation_tool.ui.screens.labeling_screen.time.time", lambda: 100.0)

    screen.handle_mouse_hover(5, 6)
    assert session.cursor_x == 5
    assert session.cursor_y == 6

    screen.handle_key_press("w")
    assert session.current_item_id() == 1

    screen.handle_key_press("q")
    assert session.current_item_id() == 1

    monkeypatch.setattr("annotation_tool.ui.screens.labeling_screen.time.time", lambda: 101.0)
    screen.handle_key_press("q")
    assert session.current_item_id() == 0

    screen.handle_key_press("shift")
    assert session.controller.shift_mode is True

    screen.handle_key_release("shift")
    assert session.controller.shift_mode is False
