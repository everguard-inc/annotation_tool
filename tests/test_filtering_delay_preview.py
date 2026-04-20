import numpy as np

from annotation_tool.core.enums import FilteringDelay
from annotation_tool.infrastructure.repositories.filtering_repository import FilteringRepository
from annotation_tool.services.filtering_session import FilteringSession


class ColorFrameProvider:
    def open(self) -> None:
        pass

    def frame_count(self) -> int:
        return 2

    def request_frame(self, index: int):
        frame = np.zeros((40, 40, 3), dtype=np.uint8)
        frame[:, :20] = (0, 0, 255)
        frame[:, 20:] = (0, 255, 0)
        return frame

    def prefetch(self, start_index: int, direction: int) -> None:
        pass

    def close(self) -> None:
        pass


class EmptyDecoder:
    def decode_image_name(self, frame):
        return None


def test_delay_setting_and_preview_modes_change_filtering_frame(data_dir, filtering_project, filtering_paths) -> None:
    """Covers FR-160, FR-161, FR-162, FR-157."""
    repository = FilteringRepository(data_dir, filtering_project.id)
    session = FilteringSession(ColorFrameProvider(), repository, EmptyDecoder())

    session.set_delay(FilteringDelay.NO_DELAY)
    assert session.status().delay == "NO_DELAY"

    normal_frame = session.current_frame()

    session.toggle_degraded_preview()
    degraded_frame = session.current_frame()

    assert not np.array_equal(normal_frame, degraded_frame)

    session.toggle_selected()
    selected_frame = session.current_frame()

    assert selected_frame[0, 0].tolist() == [0, 255, 0]
