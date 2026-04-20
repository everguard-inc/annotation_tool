from PySide6.QtCore import QPoint

from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.ui.widgets.class_wheel_overlay import ClassWheelOverlay


def test_class_hotkeys_and_wheel_selection_change_active_and_selected_labels(
    qapp,
    data_dir,
    object_project,
    rich_labeling_cache,
) -> None:
    """Covers FR-139, FR-140, FR-141, FR-142, FR-196."""
    repository = LabelingRepository(data_dir, object_project.id)
    session = LabelingSession(object_project, repository)

    session.set_active_label_by_hotkey("1")
    session.handle_mouse_press(2, 2)
    session.handle_mouse_release(12, 12)

    session.set_active_label_by_hotkey("4")
    assert session.controller.figures()[0].label == "truck"

    wheel = ClassWheelOverlay()
    labels = session.labels()
    wheel.open_at(QPoint(10, 10), labels)
    selected = wheel.selected_label(QPoint(20, 10))

    assert selected.name == "car"
    assert [label.hotkey for label in labels] == ["1", "2", "3", "4"]
