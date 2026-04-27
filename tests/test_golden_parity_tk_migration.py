"""Golden Tk parity tests.

Tk baseline: origin/main 1dd11801066386f137f64ab2ad028005f325f463.
"""

from pathlib import Path

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui.main_window import MainWindow
from annotation_tool.ui.screens.labeling_screen import LabelingScreen
from tests.tk_era_fixture import create_tk_era_labeling_project_dir


def test_tk_era_labeling_project_opens_through_pyside_main_window(
    qapp,
    valid_settings_file: Path,
) -> None:
    settings = SettingsStore(valid_settings_file).load()
    create_tk_era_labeling_project_dir(
        settings.data_dir,
        project_id=501,
        uid="tk-501",
        item_id=0,
        labels=[
            {"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"},
            {"name": "Fix", "color": "yellow", "hotkey": "1", "type": "REVIEW_LABEL"},
        ],
        images=[
            {
                "name": "a.jpg",
                "height": 20,
                "width": 30,
                "bboxes": [{"x1": 2, "y1": 3, "x2": 10, "y2": 12, "label": "car"}],
                "review_labels": [{"x": 5, "y": 6, "label": "Fix"}],
            }
        ],
        create_images=True,
    )
    window = MainWindow(SettingsStore(valid_settings_file))
    project = ProjectData(
        id=501,
        uid="tk-501",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )

    window._set_project_screen(project)

    assert isinstance(window.current_screen, LabelingScreen)
    assert window.current_screen.session.item_count() == 1
    assert window.current_screen.session.controller.figures()[0].label == "car"
    assert window.current_screen.session.review_figures[0].label == "Fix"
