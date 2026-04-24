from pathlib import Path

from annotation_tool.core.enums import FigureType
from annotation_tool.core.models import LabelData
from annotation_tool.infrastructure.repositories.labeling_repository import (
    LabelingRepository,
)
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.ui.screens.labeling_screen import LabelingScreen
from annotation_tool.ui.widgets.classes_html import labels_to_html
from annotation_tool.ui.widgets.html_window import HtmlWindow


def test_classes_html_contains_hotkeys_names_types_and_colors(
    data_dir, object_project, rich_labeling_cache
) -> None:
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


def test_classes_html_expands_keypoint_names_and_colors_from_label_attributes() -> None:
    """Covers FR-198."""
    html = labels_to_html(
        "Classes",
        [
            LabelData(
                name="pose",
                color="blue",
                hotkey="2",
                type=FigureType.KGROUP,
                attributes=(
                    '{"keypoint_info": {'
                    '"head": {"x": 0.5, "y": 0.0, "color": "yellow"}, '
                    '"tail": {"x": 0.5, "y": 1.0, "color": "cyan"}}}'
                ),
            )
        ],
    )

    assert "<td>head</td>" in html
    assert "<td>tail</td>" in html
    assert "<td>KEYPOINT</td>" in html
    assert "<td>yellow</td>" in html
    assert "<td>cyan</td>" in html


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
    html_path.write_text(
        "<h1>How to use this tool</h1><p>Use hotkeys.</p>", encoding="utf-8"
    )

    window = HtmlWindow("How to use this tool?", html_path)

    browser = window.centralWidget()
    assert "How to use this tool" in browser.toPlainText()
    assert "Use hotkeys" in browser.toPlainText()


def test_bundled_help_templates_exist_at_expected_path() -> None:
    """Covers FR-042, FR-043, FR-044. Regression for the 2026-04-23 find
    that templates/how.html and templates/hotkeys.html were missing from
    the PySide worktree, causing Help menu items to show the
    'Documentation page is missing.' fallback. The files must be present
    at the exact path MainWindow resolves them against."""
    from annotation_tool.ui import main_window as main_window_module

    repo_root = Path(main_window_module.__file__).resolve().parents[2]
    how_path = repo_root / "templates" / "how.html"
    hotkeys_path = repo_root / "templates" / "hotkeys.html"

    assert how_path.exists(), f"missing bundled help template: {how_path}"
    assert hotkeys_path.exists(), f"missing bundled hotkeys template: {hotkeys_path}"
    assert how_path.stat().st_size > 0
    assert hotkeys_path.stat().st_size > 0


def test_bundled_help_templates_render_real_content_not_the_missing_fallback(
    qapp,
) -> None:
    """Covers FR-042, FR-043, FR-044. HtmlWindow falls back to
    'Documentation page is missing.' when the template path does not
    resolve. Drive HtmlWindow against the production template paths and
    assert the fallback text is NOT present."""
    from annotation_tool.ui import main_window as main_window_module

    repo_root = Path(main_window_module.__file__).resolve().parents[2]

    for file_name, title in (
        ("how.html", "How to use this tool?"),
        ("hotkeys.html", "Hotkeys"),
    ):
        path = repo_root / "templates" / file_name
        window = HtmlWindow(title, path)
        text = window.centralWidget().toPlainText()
        assert "Documentation page is missing" not in text, (
            f"{file_name} is resolving through the missing-file fallback"
        )
        assert len(text.strip()) > 0
