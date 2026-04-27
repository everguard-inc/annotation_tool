"""Offscreen status-bar content-shape, update-regularly, and adaptive-font tests.

Covers FR-144, FR-145, FR-146, FR-163.
"""

from annotation_tool.core.models import FilteringStatusData, LabelingStatusData
from annotation_tool.ui.widgets.status_bar_filtering import FilteringStatusBar
from annotation_tool.ui.widgets.status_bar_labeling import LabelingStatusBar


def _labeling_status(**overrides) -> LabelingStatusData:
    base = dict(
        item_id=2,
        items_count=10,
        duration_hours=0.75,
        speed_per_hour=12.0,
        processed_count=3,
        selected_class="car",
        class_color="red",
        is_trash=False,
        annotation_mode="OBJECT_DETECTION",
        annotation_stage="ANNOTATE",
        figures_hidden=False,
        review_labels_hidden=False,
    )
    base.update(overrides)
    return LabelingStatusData(**base)


def _filtering_status(**overrides) -> FilteringStatusData:
    base = dict(
        item_id=4,
        items_count=20,
        duration_hours=0.25,
        speed_per_hour=8.0,
        processed_count=5,
        delay="SHORT",
        selected=True,
        selected_count=2,
    )
    base.update(overrides)
    return FilteringStatusData(**base)


def test_labeling_status_bar_renders_full_content_shape(qapp) -> None:
    """Covers FR-144."""
    bar = LabelingStatusBar()
    bar.update_status(_labeling_status())

    assert bar.mode_label.text() == "Mode: OBJECT_DETECTION: ANNOTATE"
    assert bar.class_label.text() == "Class: car"
    assert bar.trash_label.text() == "not Trash"
    assert bar.hidden_label.text() == "All Visible"
    assert bar.item_id_label.text() == "Img id: 2"
    assert "Speed: 12" in bar.speed_label.text()
    assert bar.progress_bar.value() == 30  # (2+1)/10 * 100
    assert bar.processed_label.text() == "Position: 30 % (3/10)"
    assert bar.duration_label.text() == "Duration: 0.75 hours"


def test_labeling_status_bar_hidden_state_cycles_through_modes(qapp) -> None:
    """Covers FR-144 (hidden-state branch coverage)."""
    bar = LabelingStatusBar()

    bar.update_status(_labeling_status(figures_hidden=True))
    assert bar.hidden_label.text() == "All Hidden"

    bar.update_status(_labeling_status(review_labels_hidden=True))
    assert bar.hidden_label.text() == "Review Hidden"

    bar.update_status(_labeling_status(is_trash=True))
    assert bar.trash_label.text() == "Trash"


def test_labeling_status_bar_updates_on_repeated_calls(qapp) -> None:
    """Covers FR-146. The status bar must reflect the latest StatusData
    on every update_status call, not just the first."""
    bar = LabelingStatusBar()

    bar.update_status(_labeling_status(item_id=0, duration_hours=0.0))
    first_item = bar.item_id_label.text()
    first_duration = bar.duration_label.text()
    first_progress = bar.progress_bar.value()

    bar.update_status(_labeling_status(item_id=7, duration_hours=1.5))

    assert bar.item_id_label.text() != first_item
    assert bar.item_id_label.text() == "Img id: 7"
    assert bar.duration_label.text() != first_duration
    assert bar.duration_label.text() == "Duration: 1.50 hours"
    assert bar.progress_bar.value() != first_progress


def test_filtering_status_bar_renders_full_content_shape(qapp) -> None:
    """Covers FR-163."""
    bar = FilteringStatusBar()
    bar.update_status(_filtering_status())

    assert bar.mode_label.text() == "Mode: Filtering"
    assert bar.delay_label.text() == "Delay: SHORT"
    assert bar.selected_label.text() == "Selected: TRUE"
    assert bar.item_id_label.text() == "Img id: 4"
    assert "Speed: 8" in bar.speed_label.text()
    assert "Selected: 40" in bar.selected_ratio_label.text()  # 2/5 * 100
    assert bar.processed_label.text() == "Position: 25 % (5/20)"
    assert bar.progress_bar.value() == 25
    assert bar.duration_label.text() == "Duration: 0.25 hours"


def test_filtering_status_bar_updates_on_repeated_calls(qapp) -> None:
    """Covers FR-146 for filtering mode."""
    bar = FilteringStatusBar()

    bar.update_status(_filtering_status(item_id=0, selected=False))
    before_selected = bar.selected_label.text()
    before_progress = bar.progress_bar.value()

    bar.update_status(_filtering_status(item_id=9, selected=True))

    assert bar.selected_label.text() != before_selected
    assert bar.selected_label.text() == "Selected: TRUE"
    assert bar.progress_bar.value() != before_progress


def test_labeling_status_bar_scales_font_with_width(qapp) -> None:
    """Covers FR-145. Status-bar label point-size clamps to [8, 15] and
    tracks int(width / 130) between the bounds. Offscreen delivery
    requires show() + processEvents() before the resize dispatches."""
    bar = LabelingStatusBar()
    bar.show()
    qapp.processEvents()

    scaling_labels = (
        bar.mode_label,
        bar.class_label,
        bar.trash_label,
        bar.hidden_label,
        bar.item_id_label,
        bar.speed_label,
        bar.processed_label,
        bar.duration_label,
    )

    cases = [(300, 8), (1690, 13), (3000, 15)]
    for width, expected in cases:
        bar.resize(width, 30)
        qapp.processEvents()
        for label in scaling_labels:
            assert label.font().pointSize() == expected, (
                f"width={width} label={label.objectName() or label.text()} "
                f"got {label.font().pointSize()} expected {expected}"
            )


def test_filtering_status_bar_scales_font_with_width(qapp) -> None:
    """Covers FR-145 for filtering mode. Same clamp and divisor as the
    labeling bar; offscreen delivery requires show() + processEvents()
    before the resize dispatches."""
    bar = FilteringStatusBar()
    bar.show()
    qapp.processEvents()

    scaling_labels = (
        bar.mode_label,
        bar.delay_label,
        bar.selected_label,
        bar.item_id_label,
        bar.speed_label,
        bar.selected_ratio_label,
        bar.processed_label,
        bar.duration_label,
    )

    cases = [(300, 8), (1690, 13), (3000, 15)]
    for width, expected in cases:
        bar.resize(width, 30)
        qapp.processEvents()
        for label in scaling_labels:
            assert label.font().pointSize() == expected, (
                f"width={width} label={label.objectName() or label.text()} "
                f"got {label.font().pointSize()} expected {expected}"
            )
