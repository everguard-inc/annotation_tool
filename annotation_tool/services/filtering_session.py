import numpy as np

from annotation_tool.core.enums import FilteringDelay
from annotation_tool.core.models import FilteringStatusData
from annotation_tool.infrastructure.repositories.filtering_repository import FilteringRepository
from annotation_tool.media.barcode_decoder import BarcodeDecoder
from annotation_tool.media.image_converter import deteriorate_image
from annotation_tool.media.video_frame_provider import VideoFrameProvider


class FilteringSession:
    def __init__(
        self,
        frame_provider: VideoFrameProvider,
        repository: FilteringRepository,
        barcode_decoder: BarcodeDecoder | None = None,
    ) -> None:
        self.frame_provider = frame_provider
        self.repository = repository
        self.barcode_decoder = barcode_decoder or BarcodeDecoder()

        self.item_id = 0
        self.duration_hours = 0.0
        self.processed_item_ids: set[int] = set()
        self.delay = FilteringDelay.SHORT
        self.make_image_worse = False
        self.current_name: str | None = None

        self.frame_provider.open()
        self.load_current_item()

    def item_count(self) -> int:
        return self.frame_provider.frame_count()

    def current_item_id(self) -> int:
        return self.item_id

    def status(self) -> FilteringStatusData:
        return FilteringStatusData(
            item_id=self.item_id,
            items_count=max(self.item_count(), 1),
            duration_hours=self.duration_hours,
            speed_per_hour=round(len(self.processed_item_ids) / (self.duration_hours + 1e-7), 2),
            processed_count=len(self.processed_item_ids),
            delay=self.delay.name,
            selected=self.repository.get_selected(self.item_id, self.current_name),
            selected_count=self.repository.count_selected(),
        )

    def current_frame(self) -> np.ndarray:
        frame = self.frame_provider.request_frame(self.item_id).copy()

        if self.make_image_worse:
            frame = deteriorate_image(frame)

        if self.repository.get_selected(self.item_id, self.current_name):
            h, w = frame.shape[:2]
            import cv2

            cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 255, 0), 10)

        return frame

    def load_current_item(self) -> None:
        frame = self.frame_provider.request_frame(self.item_id)
        self.current_name = self.barcode_decoder.decode_image_name(frame)
        self.repository.save_item_name(self.item_id, self.current_name)

    def go_to_item(self, item_id: int) -> None:
        if self.item_count() == 0:
            return

        self.save_current_item()
        self.processed_item_ids.add(self.item_id)
        self.item_id = max(0, min(item_id, self.item_count() - 1))
        self.load_current_item()

    def next_item(self) -> None:
        self.go_to_item(self.item_id + 1)

    def previous_item(self) -> None:
        self.go_to_item(self.item_id - 1)

    def toggle_selected(self) -> None:
        self.repository.toggle_selected(self.item_id, self.current_name)

    def go_to_next_selected(self) -> None:
        for item_id, _ in self.repository.list_selected():
            if item_id is not None and item_id > self.item_id:
                self.go_to_item(item_id)
                return

    def go_to_previous_selected(self) -> None:
        for item_id, _ in reversed(self.repository.list_selected()):
            if item_id is not None and item_id < self.item_id:
                self.go_to_item(item_id)
                return

    def set_delay(self, delay: FilteringDelay) -> None:
        self.delay = delay

    def toggle_degraded_preview(self) -> None:
        self.make_image_worse = not self.make_image_worse

    def save_current_item(self) -> None:
        self.repository.save_item_name(self.item_id, self.current_name)

    def close(self) -> None:
        self.save_current_item()
        if hasattr(self.repository, "flush"):
            self.repository.flush()
        self.frame_provider.close()
