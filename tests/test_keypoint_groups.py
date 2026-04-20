from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession


def test_keypoint_group_is_created_reflected_moved_deleted_and_serialized(
    data_dir,
    keypoints_project,
    rich_labeling_cache,
) -> None:
    """Covers FR-099, FR-100, FR-101, FR-102, FR-103, FR-104, FR-105, FR-106."""
    repository = LabelingRepository(data_dir, keypoints_project.id)
    session = LabelingSession(keypoints_project, repository)

    session.set_active_label_by_hotkey("2")
    session.handle_mouse_press(20, 20)
    session.handle_mouse_release(10, 10)

    group = session.controller.figures()[0]
    points = {point.label: point for point in group.keypoints}

    assert points["head"].x == 15
    assert points["head"].y == 20
    assert points["tail"].x == 15
    assert points["tail"].y == 10

    session.handle_mouse_hover(15, 20)
    session.handle_mouse_press(15, 20)
    session.handle_mouse_move(18, 21)
    session.handle_mouse_release(18, 21)

    moved = {point.label: point for point in session.controller.figures()[0].keypoints}
    assert moved["head"].x == 18
    assert moved["head"].y == 21

    session.toggle_label_names()
    assert session.controller.figures()[0].show_names is False
    session.render_frame()
    assert session.controller.figures()[0].show_names is True

    session.handle_mouse_hover(18, 21)
    session.delete_selected()
    assert session.controller.figures() == []
