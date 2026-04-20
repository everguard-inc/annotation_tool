from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession


def test_image_lists_match_annotation_review_and_correction_rules(
    data_dir,
    object_project,
    review_project,
    correction_project,
    rich_labeling_cache,
) -> None:
    """Covers FR-063, FR-064, FR-065."""
    repository = LabelingRepository(data_dir, object_project.id)

    annotation_session = LabelingSession(object_project, repository)
    review_session = LabelingSession(review_project, repository)
    correction_session = LabelingSession(correction_project, repository)

    assert annotation_session.image_names == ["a.jpg", "b.jpg", "c.jpg"]
    assert review_session.image_names == ["a.jpg", "c.jpg"]
    assert correction_session.image_names == ["b.jpg", "c.jpg"]
