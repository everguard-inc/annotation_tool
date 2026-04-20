from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession


def test_trash_is_blocked_during_review_and_review_labels_are_one_click_annotations(
    data_dir,
    object_project,
    review_project,
    rich_labeling_cache,
) -> None:
    """Covers FR-089, FR-090, FR-091, FR-092, FR-093."""
    repository = LabelingRepository(data_dir, object_project.id)

    annotation_session = LabelingSession(object_project, repository)
    annotation_session.toggle_trash()
    assert annotation_session.status().is_trash is True

    review_session = LabelingSession(review_project, repository)
    review_session.toggle_trash()
    assert review_session.status().is_trash is False

    review_session.set_active_label_by_hotkey("1")
    review_session.handle_mouse_press(11, 12)
    review_session.save_current_item()

    annotations = repository.load_image_annotations(review_session.image_names[review_session.item_id])
    assert {"x": 11, "y": 12, "label": "Fix object"} in annotations["review"]
