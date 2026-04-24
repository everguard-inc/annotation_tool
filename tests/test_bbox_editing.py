from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession


def test_bbox_can_be_created_selected_resized_relabelled_and_deleted(
    data_dir,
    object_project,
    rich_labeling_cache,
) -> None:
    """Covers FR-070, FR-071, FR-072, FR-073, FR-074, FR-075, FR-076, FR-082, FR-083, FR-084, FR-194."""
    repository = LabelingRepository(data_dir, object_project.id)
    session = LabelingSession(object_project, repository)

    session.set_active_label_by_hotkey("1")
    session.handle_mouse_press(2, 3)
    session.handle_mouse_release(20, 15)

    assert len(session.controller.figures()) == 1
    bbox = session.controller.figures()[0]
    assert bbox.serialize() == {"x1": 2, "y1": 3, "x2": 20, "y2": 15, "label": "car"}

    session.handle_mouse_hover(2, 3)
    session.handle_mouse_press(2, 3)
    session.handle_mouse_move(4, 5)
    session.handle_mouse_release(4, 5)

    bbox = session.controller.figures()[0]
    assert bbox.x1 == 4
    assert bbox.y1 == 5

    session.set_active_label_by_hotkey("4")
    assert session.controller.figures()[0].label == "truck"

    session.delete_selected()
    assert session.controller.figures() == []

    session.handle_mouse_press(1, 1)
    session.handle_mouse_release(10, 10)
    session.delete_all()
    assert session.controller.figures() == []


def test_bbox_creation_shows_live_preview_while_dragging(
    data_dir,
    object_project,
    rich_labeling_cache,
) -> None:
    repository = LabelingRepository(data_dir, object_project.id)
    session = LabelingSession(object_project, repository)

    session.set_active_label_by_hotkey("1")
    session.handle_mouse_press(2, 3)
    session.handle_mouse_move(20, 15)

    assert session.controller.figures() == []
    preview = session.controller.preview
    assert preview is not None
    assert preview.serialize() == {"x1": 2, "y1": 3, "x2": 20, "y2": 15, "label": "car"}

    session.handle_mouse_release(20, 15)

    assert session.controller.preview is None
    assert session.controller.figures()[0].serialize() == {
        "x1": 2,
        "y1": 3,
        "x2": 20,
        "y2": 15,
        "label": "car",
    }
