from pathlib import Path

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import FilteringPaths, LabelingPaths
from annotation_tool.core.utils import read_json, write_json
from annotation_tool.services.import_export_service import ImportExportService


class UnusedFileTransfer:
    def download(self, *args, **kwargs):
        raise AssertionError("Download is not expected here")

    def upload(self, *args, **kwargs):
        raise AssertionError("Upload is not expected here")


def test_export_writes_labeling_annotations_and_selected_filtering_frames(
    data_dir: Path,
    labeling_project,
    filtering_project,
) -> None:
    """Covers FR-094, FR-095, FR-114, FR-164, FR-165."""
    service = ImportExportService(data_dir=data_dir, file_transfer=UnusedFileTransfer())

    labeling_paths = LabelingPaths(data_dir, labeling_project.id)
    labeling_paths.ensure_project_dir()
    write_json(
        labeling_paths.cache_path,
        {
            "figures": {
                "img1.jpg": {
                    "trash": False,
                    "bboxes": [{"x1": 1, "y1": 2, "x2": 3, "y2": 4, "label": "car"}],
                    "masks": {"road": "0:10"},
                    "kgroups": [],
                    "height": 10,
                    "width": 10,
                }
            },
            "review": {"img1.jpg": [{"label": "Fix", "x": 1, "y": 2}]},
        },
    )

    filtering_paths = FilteringPaths(data_dir, filtering_project.id)
    filtering_paths.ensure_project_dir()
    write_json(
        filtering_paths.cache_path,
        {
            "items": [
                {"item_id": 1, "name": "a.jpg", "selected": True},
                {"item_id": 2, "name": None, "selected": True},
                {"item_id": 3, "name": "c.jpg", "selected": False},
            ]
        },
    )

    figures_path = service.export_figures(labeling_project)
    review_path = service.export_review_labels(labeling_project)
    selected_path = service.export_selected_frames(filtering_project)

    assert read_json(figures_path)["img1.jpg"]["masks"] == {"road": "0:10"}
    assert read_json(review_path)["img1.jpg"][0]["label"] == "Fix"
    assert read_json(selected_path) == {"names": ["a.jpg"], "ids": [2]}


def test_labeling_export_results_matches_tk_stage_specific_upload_contract(
    data_dir: Path,
    labeling_project,
) -> None:
    service = ImportExportService(data_dir=data_dir, file_transfer=UnusedFileTransfer())
    paths = LabelingPaths(data_dir, labeling_project.id)
    paths.ensure_project_dir()
    write_json(
        paths.cache_path,
        {
            "figures": {"img1.jpg": {"bboxes": [], "masks": {}, "kgroups": []}},
            "review": {"img1.jpg": [{"label": "Fix", "x": 1, "y": 2}]},
        },
    )
    review_project = ProjectData(
        id=labeling_project.id,
        uid=labeling_project.uid,
        stage=AnnotationStage.REVIEW,
        mode=AnnotationMode.OBJECT_DETECTION,
    )

    annotate_result = service.export_results(labeling_project)
    review_result = service.export_results(review_project)

    assert annotate_result == [paths.figures_path]
    assert review_result == [paths.review_path]
