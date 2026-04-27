"""Enum-membership assertions that back the workbook FRs listing supported
annotation modes and stages. EV membership is active in the Linux PySide
scope and is routed through the normal project screen layer."""

from annotation_tool.core.enums import AnnotationMode, AnnotationStage


def test_annotation_mode_enum_covers_frozen_fr_catalogue() -> None:
    """Covers FR-009."""
    assert {mode.name for mode in AnnotationMode} >= {
        "OBJECT_DETECTION",
        "SEGMENTATION",
        "KEYPOINTS",
        "FILTERING",
        "EVENT_VALIDATION",
    }


def test_annotation_stage_enum_covers_frozen_fr_catalogue() -> None:
    """Covers FR-010."""
    assert {stage.name for stage in AnnotationStage} >= {
        "ANNOTATE",
        "REVIEW",
        "CORRECTION",
        "SENT_FOR_REVIEW",
        "SENT_FOR_CORRECTION",
        "DONE",
        "FILTERING",
        "EVENT_VALIDATION",
        "UNKNOWN",
    }
