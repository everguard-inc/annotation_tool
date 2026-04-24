"""Golden overwrite and live-settings parity tests.

Tk baseline: origin/main 1dd11801066386f137f64ab2ad028005f325f463.
"""

from dataclasses import replace
from pathlib import Path

from PySide6.QtWidgets import QDialog, QMessageBox

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import LabelingPaths
from annotation_tool.core.settings import SettingsStore
from annotation_tool.core.utils import read_json, write_json
from annotation_tool.infrastructure.repositories.labeling_repository import (
    LabelingRepository,
)
from annotation_tool.infrastructure.repositories.project_repository import (
    ProjectRepository,
)
from annotation_tool.services.import_export_service import ImportExportService
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.services.project_service import ProjectService
from annotation_tool.ui import main_window as main_window_module
from annotation_tool.ui.main_window import MainWindow
from annotation_tool.ui.screens.labeling_screen import LabelingScreen
from tests.conftest import create_pattern_image
from tests.tk_era_fixture import create_tk_era_labeling_project_dir


def test_open_settings_applies_interface_style_to_real_labeling_session(
    qapp,
    valid_settings_file: Path,
    monkeypatch,
) -> None:
    store = SettingsStore(valid_settings_file)
    settings = store.load()
    create_tk_era_labeling_project_dir(
        settings.data_dir,
        project_id=702,
        uid="uid-702",
        item_id=0,
        labels=[{"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"}],
        images=[
            {
                "name": "a.jpg",
                "height": 10,
                "width": 20,
                "bboxes": [{"x1": 2, "y1": 2, "x2": 8, "y2": 7, "label": "car"}],
            }
        ],
        create_images=True,
    )
    project = ProjectData(
        id=702,
        uid="uid-702",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    window = MainWindow(store)
    window._set_project_screen(project)
    assert isinstance(window.current_screen, LabelingScreen)
    screen = window.current_screen
    assert screen.session.controller.annotation_style.bbox_line_width == 3.0

    new_settings = replace(
        settings,
        bbox_line_width=8.0,
        cursor_proximity_threshold=9.0,
        objects_opacity=0.5,
        color_fill_opacity=0.25,
        bbox_handler_size=7.0,
        keypoint_handler_size=6.0,
    )

    class AcceptedSettingsDialog:
        DialogCode = QDialog.DialogCode

        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return QDialog.DialogCode.Accepted

        def settings(self):
            return new_settings

    monkeypatch.setattr(main_window_module, "SettingsDialog", AcceptedSettingsDialog)

    window.open_settings()

    assert screen.session.annotation_style.bbox_line_width == 8.0
    assert screen.session.annotation_style.cursor_proximity_threshold == 9.0
    assert screen.session.controller.annotation_style.bbox_line_width == 8.0
    assert screen.session.controller.annotation_style.cursor_proximity_threshold == 9.0


class ReachableApi:
    def is_available(self) -> bool:
        return True


class DownloadingTransfer:
    def __init__(self, paths: LabelingPaths) -> None:
        self.paths = paths

    def download(self, uid: str, file_name: str, destination: Path, **kwargs) -> None:
        if file_name == self.paths.figures_path.name:
            write_json(
                destination,
                {
                    "a.jpg": {
                        "trash": False,
                        "bboxes": [
                            {"x1": 9, "y1": 1, "x2": 18, "y2": 8, "label": "truck"}
                        ],
                        "masks": {},
                        "kgroups": [],
                        "height": 10,
                        "width": 20,
                    }
                },
            )
            return

        if file_name == self.paths.review_path.name:
            write_json(destination, {})
            return

        if file_name == self.paths.meta_path.name:
            write_json(
                destination,
                {
                    "labels": [
                        {
                            "name": "truck",
                            "color": "blue",
                            "hotkey": "2",
                            "type": "BBOX",
                        }
                    ],
                    "review_labels": [],
                },
            )
            return

        raise AssertionError(f"unexpected download: {file_name}")


def test_overwrite_refreshes_real_labeling_session_without_stale_save(
    qapp,
    valid_settings_file: Path,
    monkeypatch,
) -> None:
    settings = SettingsStore(valid_settings_file).load()
    project = ProjectData(
        id=701,
        uid="uid-701",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    paths = LabelingPaths(settings.data_dir, project.id)
    paths.ensure_project_dir()
    paths.images_dir.mkdir(parents=True, exist_ok=True)
    create_pattern_image(
        paths.images_dir / "a.jpg", size=(20, 10), base=(255, 255, 255)
    )
    write_json(
        paths.cache_path,
        {
            "labels": [
                {"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"}
            ],
            "review_labels": [],
            "items": [
                {
                    "name": "a.jpg",
                    "width": 20,
                    "height": 10,
                    "requires_annotation": True,
                }
            ],
            "figures": {
                "a.jpg": {
                    "trash": False,
                    "bboxes": [{"x1": 2, "y1": 2, "x2": 8, "y2": 7, "label": "car"}],
                    "masks": {},
                    "kgroups": [],
                    "height": 10,
                    "width": 20,
                }
            },
            "review": {},
        },
    )

    window = MainWindow(SettingsStore(valid_settings_file))
    repository = LabelingRepository(settings.data_dir, project.id)
    session = LabelingSession(project, repository)
    screen = LabelingScreen(session)
    transfer = DownloadingTransfer(paths)
    window.current_project = project
    window.current_screen = screen
    window.api_client = ReachableApi()
    window.project_service = ProjectService(
        api_client=window.api_client,
        project_repository=ProjectRepository(settings.data_dir),
        import_export_service=ImportExportService(settings.data_dir, transfer),
    )

    class Progress:
        def update_progress(self, *args):
            pass

        def should_cancel(self):
            return False

        def mark_complete(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(window, "_progress", lambda title: Progress())
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "information",
        lambda *args, **kwargs: None,
    )

    window.overwrite_annotations()

    reloaded = session.controller.figures()
    assert len(reloaded) == 1
    assert (reloaded[0].x1, reloaded[0].y1, reloaded[0].x2, reloaded[0].y2) == (
        9,
        1,
        18,
        8,
    )
    assert reloaded[0].label == "truck"
    refreshed_label_names = {label.name for label in session.figure_labels}
    assert "truck" in refreshed_label_names
    assert "car" not in refreshed_label_names
    persisted = read_json(paths.cache_path)
    assert persisted["figures"]["a.jpg"]["bboxes"] == [
        {"x1": 9, "y1": 1, "x2": 18, "y2": 8, "label": "truck"}
    ]
