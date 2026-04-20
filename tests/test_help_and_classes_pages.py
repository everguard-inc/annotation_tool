from pathlib import Path

from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.ui.screens.labeling_screen import LabelingScreen
from annotation_tool.ui.widgets.classes_html import labels_to_html
from annotation_tool.ui.widgets.html_window import HtmlWindow


def test_classes_html_contains_hotkeys_names_types_and_colors(data_dir, object_project, rich_labeling_cache) -> None:
    """Covers FR-045, FR-046, FR-197, FR-198."""
    repository = LabelingRepository(data_dir, object_project.id)

    html = labels_to_html("Classes", repository.get_figure_labels())

    assert "Classes" in html
    assert "<td>1</td>" in html
    assert "<td>car</td>" in html
    assert "<td>BBOX</td>" in html
    assert "<td>red</td>" in html
    assert "<td>3</td>" in html
    assert "<td>MASK</td>" in html


def test_labeling_screen_opens_classes_and_review_labels_windows(
    qapp,
    data_dir,
    object_project,
    rich_labeling_cache,
) -> None:
    """Covers FR-045, FR-046."""
    repository = LabelingRepository(data_dir, object_project.id)
    session = LabelingSession(object_project, repository)
    screen = LabelingScreen(session)

    screen.show_classes()
    screen.show_review_labels()

    assert screen._classes_window.windowTitle() == "Classes"
    assert screen._review_labels_window.windowTitle() == "Review Labels"


def test_html_window_loads_documentation_file(qapp, tmp_path: Path) -> None:
    """Covers FR-042, FR-043, FR-044."""
    html_path = tmp_path / "how.html"
    html_path.write_text("<h1>How to use this tool</h1><p>Use hotkeys.</p>", encoding="utf-8")

    window = HtmlWindow("How to use this tool?", html_path)

    browser = window.centralWidget()
    assert "How to use this tool" in browser.toPlainText()
    assert "Use hotkeys" in browser.toPlainText()
