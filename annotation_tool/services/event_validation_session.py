from collections import OrderedDict
from dataclasses import dataclass

import cv2
import numpy as np

from annotation_tool.core.enums import AnnotationStage
from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.core.models import ProjectData
from annotation_tool.infrastructure.repositories.event_validation_repository import (
    EventValidationRepository,
)
from annotation_tool.services.session_state import SessionState, SessionStateStore
from annotation_tool.services.statistics_service import StatisticsService

MAX_EVENT_VALIDATION_VIDEO_FRAMES = 1000


@dataclass
class EventValidationStatusData:
    item_id: int
    items_count: int
    duration_hours: float
    speed_per_hour: float
    processed_count: int
    view_mode: str
    number_of_frames: int
    current_frame_number: int


class EventValidationSession:
    def __init__(
        self,
        project: ProjectData,
        repository: EventValidationRepository,
        session_state_store: SessionStateStore | None = None,
        statistics_service: StatisticsService | None = None,
    ) -> None:
        self.project = project
        self.repository = repository
        self.session_state_store = session_state_store
        self.statistics_service = statistics_service
        self.event_uids = [event["uid"] for event in repository.events()]

        state = (
            session_state_store.load()
            if session_state_store
            else SessionState(0, 0.0, set())
        )
        self.item_id = min(state.item_id, max(len(self.event_uids) - 1, 0))
        self.duration_hours = state.duration_hours
        self.processed_item_ids = set(state.processed_item_ids)
        if self.statistics_service is not None:
            self.statistics_service.duration_hours = self.duration_hours

        self.fields = repository.fields()
        self.questions = list(self.fields.keys())
        self.answers = OrderedDict((question, "") for question in self.questions)
        self.comment = ""
        self.frames: list[np.ndarray] = []
        self.image: np.ndarray | None = None
        self.current_frame_number = 0
        self.video_mode_only = not self._has_images()
        self.view_mode = "VIDEO"
        self.load_current_item()

    def item_count(self) -> int:
        return len(self.event_uids)

    def current_item_id(self) -> int:
        return self.item_id

    def current_frame(self) -> np.ndarray:
        if self.view_mode == "IMAGE" and self.image is not None:
            return self.image

        if not self.frames:
            raise UserVisibleError("Unable to load event validation video frames.")

        return self.frames[self.current_frame_number]

    def status(self) -> EventValidationStatusData:
        return EventValidationStatusData(
            item_id=self.item_id,
            items_count=max(self.item_count(), 1),
            duration_hours=self.duration_hours,
            speed_per_hour=round(
                len(self.processed_item_ids) / (self.duration_hours + 1e-7), 2
            ),
            processed_count=len(self.processed_item_ids),
            view_mode=self.view_mode,
            number_of_frames=len(self.frames),
            current_frame_number=self.current_frame_number + 1,
        )

    def load_current_item(self) -> None:
        if not self.event_uids:
            return

        event = self.repository.event(self.event_uids[self.item_id])
        stored_answers = event.get("answers", [])
        self.answers = OrderedDict(
            (
                question,
                stored_answers[index] if index < len(stored_answers) else "",
            )
            for index, question in enumerate(self.questions)
        )
        self.comment = event.get("comment", "")
        if self.view_mode == "IMAGE":
            self._load_image()
        else:
            self._load_video_frames()

    def save_current_item(self) -> None:
        if not self.event_uids:
            return

        self.repository.save_event(
            self.event_uids[self.item_id],
            list(self.answers.values()),
            self.comment,
        )

    def go_to_item(self, item_id: int) -> None:
        if not self.event_uids:
            return

        self._track_action("keyboard")
        self.save_current_item()
        self.processed_item_ids.add(self.item_id)
        self.item_id = max(0, min(item_id, self.item_count() - 1))
        self.load_current_item()
        self._persist_state()

    def next_item(self) -> None:
        self.go_to_item(self.item_id + 1)

    def previous_item(self) -> None:
        self.go_to_item(self.item_id - 1)

    def update_comment(self, comment: str) -> None:
        self._track_action("keyboard")
        self.comment = comment

    def update_answer(self, question: str, answer: str) -> None:
        self._track_action("keyboard")
        self.answers[question] = answer

    def cycle_answer(self, question: str) -> None:
        options = list(self.fields[question].keys())
        current = self.answers.get(question, "")
        next_index = (
            (options.index(current) + 1) % len(options) if current in options else 0
        )
        self.update_answer(question, options[next_index])

    def video_forward(self) -> None:
        if self.view_mode != "VIDEO":
            return

        self._track_action("keyboard")
        self.current_frame_number = min(
            self.current_frame_number + 1, len(self.frames) - 1
        )

    def video_backward(self) -> None:
        if self.view_mode != "VIDEO":
            return

        self._track_action("keyboard")
        self.current_frame_number = max(self.current_frame_number - 1, 0)

    def load_video_frame(self, frame_number: int) -> None:
        if self.view_mode != "VIDEO":
            return

        if frame_number < 0 or frame_number > len(self.frames) - 1:
            return

        self._track_action("keyboard")
        self.current_frame_number = frame_number

    def set_image_mode(self) -> None:
        if self.video_mode_only:
            return

        self._track_action("keyboard")
        self.view_mode = "IMAGE"
        self._load_image()

    def set_video_mode(self) -> None:
        self._track_action("keyboard")
        self.view_mode = "VIDEO"
        self._load_video_frames()

    def close(self) -> None:
        self.save_current_item()
        self._persist_state()

    def _load_video_frames(self) -> None:
        self.frames = []
        path = self.repository.paths.videos_dir / f"{self.event_uids[self.item_id]}.mp4"
        cap = cv2.VideoCapture(str(path))
        while True:
            if len(self.frames) >= MAX_EVENT_VALIDATION_VIDEO_FRAMES:
                break
            ok, frame = cap.read()
            if not ok:
                break
            self.frames.append(frame)
        cap.release()
        self.current_frame_number = max(0, int(len(self.frames) / 2) - 1)
        if not self.frames:
            raise UserVisibleError(f"Unable to load event validation video: {path}")

    def _load_image(self) -> None:
        path = self.repository.paths.images_dir / f"{self.event_uids[self.item_id]}.jpg"
        image = cv2.imread(str(path))
        if image is None:
            raise UserVisibleError(f"Unable to load event validation image: {path}")
        self.image = image

    def _has_images(self) -> bool:
        return (
            self.repository.paths.images_dir.exists()
            and any(self.repository.paths.images_dir.iterdir())
        )

    def _track_action(self, message: str) -> None:
        if self.statistics_service is None:
            return

        self.duration_hours = self.statistics_service.track_action(
            AnnotationStage.EVENT_VALIDATION,
            message,
        )

    def _persist_state(self) -> None:
        if self.session_state_store is None:
            return

        self.session_state_store.save(
            SessionState(self.item_id, self.duration_hours, set(self.processed_item_ids))
        )
