import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import FilteringPaths, LabelingPaths
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

def create_pattern_image(path: Path, size: tuple[int, int], base: tuple[int, int, int]) -> None:
    image = Image.new("RGB", size, color=base)
    width, height = size

    for x in range(width):
        for y in range(height):
            if (x // 4) % 2 == 0:
                image.putpixel((x, y), (255, 0, 0))
            elif (y // 3) % 2 == 0:
                image.putpixel((x, y), (0, 255, 0))
            else:
                image.putpixel((x, y), (0, 0, 255))

    image.save(path)


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

    create_pattern_image(paths.images_dir / "a.jpg", size=(20, 10), base=(255, 255, 255))
    create_pattern_image(paths.images_dir / "b.jpg", size=(20, 10), base=(220, 220, 220))

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


@pytest.fixture
def filtering_paths(data_dir: Path, filtering_project: ProjectData) -> FilteringPaths:
    paths = FilteringPaths(data_dir, filtering_project.id)
    paths.ensure_project_dir()
    write_json(paths.cache_path, {"labels": [], "review_labels": [], "items": []})
    return paths


@pytest.fixture
def filtering_video_path(filtering_paths: FilteringPaths) -> Path:
    video_path = filtering_paths.video_path
    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10,
        (32, 24),
    )

    assert writer.isOpened()
    
    for index in range(4):
        frame = np.zeros((24, 32, 3), dtype=np.uint8)
        frame[:, :] = index * 40

        for x in range(32):
            if (x // 4) % 2 == 0:
                frame[:, x] = (0, 0, 255)
            else:
                frame[:, x] = (0, 255, 0)

        cv2.putText(
            frame,
            str(index),
            (8, 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        writer.write(frame)

    writer.release()
    return video_path


@pytest.fixture
def object_project() -> ProjectData:
    return ProjectData(
        id=10,
        uid="uid-10",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )


@pytest.fixture
def review_project() -> ProjectData:
    return ProjectData(
        id=10,
        uid="uid-10",
        stage=AnnotationStage.REVIEW,
        mode=AnnotationMode.OBJECT_DETECTION,
    )


@pytest.fixture
def correction_project() -> ProjectData:
    return ProjectData(
        id=10,
        uid="uid-10",
        stage=AnnotationStage.CORRECTION,
        mode=AnnotationMode.OBJECT_DETECTION,
    )


@pytest.fixture
def keypoints_project() -> ProjectData:
    return ProjectData(
        id=10,
        uid="uid-10",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.KEYPOINTS,
    )


@pytest.fixture
def segmentation_project() -> ProjectData:
    return ProjectData(
        id=10,
        uid="uid-10",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.SEGMENTATION,
    )


@pytest.fixture
def rich_labeling_cache(data_dir: Path) -> LabelingPaths:
    paths = LabelingPaths(data_dir, 10)
    paths.ensure_project_dir()
    paths.images_dir.mkdir(parents=True, exist_ok=True)

    create_pattern_image(paths.images_dir / "a.jpg", size=(40, 30), base=(255, 255, 255))
    create_pattern_image(paths.images_dir / "b.jpg", size=(40, 30), base=(220, 220, 220))
    create_pattern_image(paths.images_dir / "c.jpg", size=(40, 30), base=(200, 200, 200))

    write_json(
        paths.cache_path,
        {
            "labels": [
                {"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"},
                {
                    "name": "pose",
                    "color": "blue",
                    "hotkey": "2",
                    "type": "KGROUP",
                    "attributes": {
                        "keypoint_info": {
                            "head": {"x": 0.5, "y": 0.0, "color": "yellow"},
                            "tail": {"x": 0.5, "y": 1.0, "color": "cyan"},
                        },
                        "keypoint_connections": [
                            {"from": "head", "to": "tail", "color": "white"}
                        ],
                    },
                },
                {"name": "road", "color": "green", "hotkey": "3", "type": "MASK"},
                {"name": "truck", "color": "blue", "hotkey": "4", "type": "BBOX"},
            ],
            "review_labels": [
                {"name": "Fix object", "color": "yellow", "hotkey": "1", "type": "REVIEW_LABEL"}
            ],
            "items": [
                {"name": "a.jpg", "width": 40, "height": 30, "requires_annotation": True},
                {"name": "b.jpg", "width": 40, "height": 30, "requires_annotation": False},
                {"name": "c.jpg", "width": 40, "height": 30, "requires_annotation": True},
            ],
            "figures": {
                "a.jpg": {"trash": False, "bboxes": [], "kgroups": [], "masks": {}, "height": 30, "width": 40},
                "b.jpg": {"trash": False, "bboxes": [], "kgroups": [], "masks": {}, "height": 30, "width": 40},
                "c.jpg": {"trash": False, "bboxes": [], "kgroups": [], "masks": {}, "height": 30, "width": 40},
            },
            "review": {
                "a.jpg": [],
                "b.jpg": [{"label": "Fix object", "x": 5, "y": 6}],
                "c.jpg": [{"label": "Fix object", "x": 7, "y": 8}],
            },
        },
    )

    return paths