import numpy as np

from annotation_tool.media.video_frame_provider import VideoFrameProvider


def test_video_provider_reads_counts_and_caches_frames(filtering_video_path) -> None:
    """Covers FR-148, FR-150, FR-151, FR-152."""
    provider = VideoFrameProvider(filtering_video_path, cache_size=2)

    provider.open()
    first_frame = provider.request_frame(0)
    cached_frame = provider.get_cached(0)

    assert provider.frame_count() == 4
    assert first_frame.shape[:2] == (24, 32)
    assert cached_frame is not None
    assert np.array_equal(first_frame, cached_frame)

    provider.prefetch(0, direction=1)
    assert provider.get_cached(1) is not None

    provider.close()
