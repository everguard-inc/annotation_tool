import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import EventValidationPaths
from annotation_tool.infrastructure.repositories.event_validation_repository import (
    EventValidationRepository,
)
from annotation_tool.services.event_validation_session import EventValidationSession


def _write_video(path: Path) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (32, 24))
    assert writer.isOpened()
    for index in range(3):
        frame = np.full((24, 32, 3), index * 60, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def _project() -> ProjectData:
    return ProjectData(
        46,
        "uid-46",
        AnnotationStage.EVENT_VALIDATION,
        AnnotationMode.EVENT_VALIDATION,
    )


def test_event_validation_session_updates_answers_comment_and_frame(
    data_dir: Path,
) -> None:
    paths = EventValidationPaths(data_dir, 46)
    paths.ensure_project_dir()
    paths.videos_dir.mkdir(parents=True)
    _write_video(paths.videos_dir / "ev-a.mp4")
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {"ev-a": {"answers": [""], "comment": ""}},
            }
        ),
        encoding="utf-8",
    )
    session = EventValidationSession(_project(), EventValidationRepository(data_dir, 46))

    session.cycle_answer("Status")
    session.update_comment("checked")
    session.video_forward()
    session.save_current_item()

    event = EventValidationRepository(data_dir, 46).event("ev-a")
    assert event["answers"] == ["TP"]
    assert event["comment"] == "checked"
    assert session.status().current_frame_number == 2


def test_event_validation_session_switches_between_video_and_image_modes(
    data_dir: Path,
) -> None:
    paths = EventValidationPaths(data_dir, 46)
    paths.ensure_project_dir()
    paths.videos_dir.mkdir(parents=True)
    paths.images_dir.mkdir(parents=True)
    _write_video(paths.videos_dir / "ev-a.mp4")
    image = np.full((24, 32, 3), 180, dtype=np.uint8)
    cv2.imwrite(str(paths.images_dir / "ev-a.jpg"), image)
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {"ev-a": {"answers": [""], "comment": ""}},
            }
        ),
        encoding="utf-8",
    )
    session = EventValidationSession(_project(), EventValidationRepository(data_dir, 46))

    session.set_image_mode()

    assert session.status().view_mode == "IMAGE"
    assert session.current_frame().shape == image.shape

    session.set_video_mode()

    assert session.status().view_mode == "VIDEO"


def test_event_validation_session_raises_user_visible_error_for_empty_video(
    data_dir: Path,
) -> None:
    paths = EventValidationPaths(data_dir, 46)
    paths.ensure_project_dir()
    paths.videos_dir.mkdir(parents=True)
    (paths.videos_dir / "ev-a.mp4").write_bytes(b"")
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {"ev-a": {"answers": [""], "comment": ""}},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(UserVisibleError, match="Unable to load event validation video"):
        EventValidationSession(_project(), EventValidationRepository(data_dir, 46))


def test_event_validation_session_caps_loaded_video_frames(
    data_dir: Path, monkeypatch
) -> None:
    paths = EventValidationPaths(data_dir, 46)
    paths.ensure_project_dir()
    paths.videos_dir.mkdir(parents=True)
    (paths.videos_dir / "ev-a.mp4").write_bytes(b"fake")
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {"ev-a": {"answers": [""], "comment": ""}},
            }
        ),
        encoding="utf-8",
    )

    class FakeCapture:
        def __init__(self, path):
            self.read_count = 0

        def read(self):
            self.read_count += 1
            if self.read_count > 1500:
                return False, None
            return True, np.zeros((4, 4, 3), dtype=np.uint8)

        def release(self):
            pass

    monkeypatch.setattr(cv2, "VideoCapture", FakeCapture)

    session = EventValidationSession(_project(), EventValidationRepository(data_dir, 46))

    assert len(session.frames) == 1000
