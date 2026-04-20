import json
import os
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "annotation-data"


@pytest.fixture
def valid_settings_file(tmp_path: Path) -> Path:
    data_dir = tmp_path / "annotation-data"
    settings_path = tmp_path / "settings.json"

    settings_path.write_text(
        json.dumps(
            {
                "general": {
                    "token": {"type": "string", "value": "token-123"},
                    "api_url": {"type": "string", "value": "https://api.example.com"},
                    "file_url": {"type": "string", "value": "https://files.example.com"},
                    "data_dir": {"type": "string", "value": str(data_dir)},
                },
                "interface": {
                    "bbox_line_width": {"type": "number", "value": 3.0},
                    "cursor_proximity_threshold": {"type": "number", "value": 3.0},
                    "objects_opacity": {"type": "number", "value": 0.9},
                    "color_fill_opacity": {"type": "number", "value": 0.1},
                    "bbox_handler_size": {"type": "number", "value": 3.0},
                    "keypoint_handler_size": {"type": "number", "value": 5.0},
                },
            }
        ),
        encoding="utf-8",
    )

    return settings_path


@pytest.fixture
def sample_project() -> ProjectData:
    return ProjectData(
        id=7,
        uid="project-uid-7",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )


@pytest.fixture
def labeling_project() -> ProjectData:
    return ProjectData(
        id=7,
        uid="uid-7",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )


@pytest.fixture
def filtering_project() -> ProjectData:
    return ProjectData(
        id=8,
        uid="uid-8",
        stage=AnnotationStage.FILTERING,
        mode=AnnotationMode.FILTERING,
    )
