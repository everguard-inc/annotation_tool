from annotation_tool.annotation.masks_encoding import decode_rle
from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession


def test_mask_polygon_can_be_added_removed_cancelled_and_saved(
    data_dir,
    segmentation_project,
    rich_labeling_cache,
) -> None:
    """Covers FR-107, FR-108, FR-109, FR-110, FR-111, FR-112, FR-113, FR-115, FR-116, FR-117."""
    repository = LabelingRepository(data_dir, segmentation_project.id)
    session = LabelingSession(segmentation_project, repository)

    session.set_active_label_by_hotkey("3")
    session.handle_mouse_press(2, 2)
    session.handle_mouse_press(20, 2)
    session.handle_mouse_press(20, 20)
    session.finish_polygon()

    mask = session.controller.figures()[0]
    assert mask.surface > 0

    session.set_shift_mode(True)
    session.handle_mouse_press(4, 4)
    session.handle_mouse_press(10, 4)
    session.handle_mouse_press(10, 10)
    session.finish_polygon()

    assert session.controller.figures()[0].surface < mask.mask.size

    session.handle_mouse_press(1, 1)
    session.handle_mouse_press(2, 2)
    assert session.controller.polygon
    session.cancel_polygon()
    assert session.controller.polygon == []

    session.delete_selected()
    assert session.controller.figures()[0].surface == 0

    session.save_current_item()
    annotations = repository.load_image_annotations("a.jpg")
    rle = annotations["figures"]["masks"]["road"]
    decoded = decode_rle(rle, width=40, height=30)

    assert decoded.shape == (30, 40)
