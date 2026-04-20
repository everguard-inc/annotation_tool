import json
import os
import sys
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import LabelingPaths
from annotation_tool.core.utils import write_json


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


@pytest.fixture
def labeling_cache(data_dir: Path, labeling_project: ProjectData) -> LabelingPaths:
    paths = LabelingPaths(data_dir, labeling_project.id)
    paths.ensure_project_dir()
    paths.images_dir.mkdir(parents=True, exist_ok=True)

    image_a = Image.new("RGB", (20, 10), color=(255, 255, 255))
    for x in range(10):
        for y in range(10):
            image_a.putpixel((x, y), (255, 0, 0))
    image_a.save(paths.images_dir / "a.jpg")

    image_b = Image.new("RGB", (20, 10), color=(255, 255, 255))
    for x in range(10, 20):
        for y in range(10):
            image_b.putpixel((x, y), (0, 0, 255))
    image_b.save(paths.images_dir / "b.jpg")

    write_json(
        paths.cache_path,
        {
            "labels": [
                {"name": "truck", "color": "blue", "hotkey": "2", "type": "BBOX"},
                {"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"},
                {"name": "blur", "color": "gray", "hotkey": "0", "type": "BBOX"},
            ],
            "review_labels": [
                {"name": "Fix", "color": "yellow", "hotkey": "1", "type": "REVIEW_LABEL"}
            ],
            "items": [
                {"name": "b.jpg", "width": 20, "height": 10, "requires_annotation": True},
                {"name": "a.jpg", "width": 20, "height": 10, "requires_annotation": True},
            ],
            "figures": {
                "a.jpg": {
                    "trash": False,
                    "bboxes": [{"x1": 2, "y1": 2, "x2": 8, "y2": 7, "label": "car"}],
                    "masks": {},
                    "kgroups": [],
                    "height": 10,
                    "width": 20,
                },
                "b.jpg": {
                    "trash": False,
                    "bboxes": [],
                    "masks": {},
                    "kgroups": [],
                    "height": 10,
                    "width": 20,
                },
            },
            "review": {},
        },
    )

    return paths