from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession


def test_objects_support_copy_paste_undo_redo_and_copy_from_previous_image(
    data_dir,
    object_project,
    rich_labeling_cache,
) -> None:
    """Covers FR-077, FR-078, FR-079, FR-080, FR-081."""
    repository = LabelingRepository(data_dir, object_project.id)
    session = LabelingSession(object_project, repository)

    session.set_active_label_by_hotkey("1")
    session.handle_mouse_press(2, 2)
    session.handle_mouse_release(12, 12)

    session.copy()
    session.paste()
    assert len(session.controller.figures()) == 2

    session.undo()
    assert len(session.controller.figures()) == 1

    session.redo()
    assert len(session.controller.figures()) == 2

    session.save_current_item()
    session.go_to_item(1)
    session.copy_from_previous_item()

    annotations = repository.load_image_annotations("b.jpg")
    assert len(annotations["figures"]["bboxes"]) == 2
