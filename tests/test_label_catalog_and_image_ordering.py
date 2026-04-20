from pathlib import Path

from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository


def test_labels_and_images_are_returned_in_stable_order(data_dir: Path, labeling_project, labeling_cache) -> None:
    """Covers FR-053, FR-054, FR-055, FR-196, FR-197, FR-198, FR-151, FR-152, FR-195."""
    repository = LabelingRepository(data_dir, labeling_project.id)

    labels = repository.get_figure_labels()
    image_names = repository.list_image_names()

    assert [label.name for label in labels] == ["blur", "car", "truck"]
    assert [label.hotkey for label in labels] == ["0", "1", "2"]
    assert image_names == ["a.jpg", "b.jpg"]