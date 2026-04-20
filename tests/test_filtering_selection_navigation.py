import numpy as np

from annotation_tool.infrastructure.repositories.filtering_repository import FilteringRepository
from annotation_tool.services.filtering_session import FilteringSession


class FakeFrameProvider:
    def __init__(self) -> None:
        self.closed = False
        self.prefetched: list[tuple[int, int]] = []

    def open(self) -> None:
        pass

    def frame_count(self) -> int:
        return 5

    def request_frame(self, index: int):
        return np.full((20, 20, 3), index * 20, dtype=np.uint8)

    def prefetch(self, start_index: int, direction: int) -> None:
        self.prefetched.append((start_index, direction))

    def close(self) -> None:
        self.closed = True


class FakeDecoder:
    def decode_image_name(self, frame):
        value = int(frame[0, 0, 0] / 20)
        return f"frame_{value}.jpg"


def test_filtering_session_navigates_and_tracks_selected_items(data_dir, filtering_project, filtering_paths) -> None:
    """Covers FR-155, FR-156, FR-157, FR-158, FR-159."""
    repository = FilteringRepository(data_dir, filtering_project.id)
    provider = FakeFrameProvider()
    session = FilteringSession(provider, repository, FakeDecoder())

    assert session.current_item_id() == 0
    assert session.current_name == "frame_0.jpg"

    session.toggle_selected()
    session.next_item()
    session.toggle_selected()
    session.next_item()

    assert session.status().selected_count == 2
    assert repository.list_selected() == [(0, "frame_0.jpg"), (1, "frame_1.jpg")]

    session.go_to_previous_selected()
    assert session.current_item_id() == 1

    session.go_to_item(0)
    session.go_to_next_selected()
    assert session.current_item_id() == 1

    assert provider.prefetched
