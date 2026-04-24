from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.core.utils import read_json, write_json
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


def test_copy_from_previous_image_only_replaces_editable_figures(
    data_dir,
    object_project,
    rich_labeling_cache,
) -> None:
    """Copy-from-previous must not copy trash/review labels during annotation."""
    cache = read_json(rich_labeling_cache.cache_path)
    cache["figures"]["a.jpg"] = {
        "trash": True,
        "bboxes": [{"x1": 1, "y1": 2, "x2": 10, "y2": 12, "label": "car"}],
        "kgroups": [],
        "masks": {},
        "height": 30,
        "width": 40,
    }
    cache["figures"]["b.jpg"]["trash"] = False
    cache["review"]["a.jpg"] = []
    cache["review"]["b.jpg"] = [{"label": "Fix object", "x": 5, "y": 6}]
    write_json(rich_labeling_cache.cache_path, cache)

    repository = LabelingRepository(data_dir, object_project.id)
    session = LabelingSession(object_project, repository)
    session.go_to_item(1)

    session.copy_from_previous_item()
    session.save_current_item()

    annotations = repository.load_image_annotations("b.jpg")
    assert annotations["figures"]["bboxes"] == [
        {"x1": 1, "y1": 2, "x2": 10, "y2": 12, "label": "car"}
    ]
    assert annotations["figures"]["trash"] is False
    assert annotations["review"] == [{"label": "Fix object", "x": 5, "y": 6}]
