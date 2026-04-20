from pathlib import Path

from annotation_tool.core.utils import now_string


class ProjectPaths:
    def __init__(self, data_dir: Path, project_id: int) -> None:
        self.data_dir = data_dir
        self.project_id = project_id
        self.project_name = str(project_id).zfill(5)

    @property
    def project_dir(self) -> Path:
        return self.data_dir / "data" / self.project_name

    @property
    def db_path(self) -> Path:
        return self.project_dir / "db.sqlite"

    @property
    def state_path(self) -> Path:
        return self.project_dir / "state.json"

    @property
    def meta_path(self) -> Path:
        return self.project_dir / "meta.json"

    @property
    def cache_path(self) -> Path:
        return self.project_dir / "cache.json"

    @property
    def runtime_state_path(self) -> Path:
        return self.project_dir / "runtime_state.json"

    @property
    def statistics_path(self) -> Path:
        existing = sorted(self.project_dir.glob("*statistics*.txt"))
        if existing:
            return existing[0]
        return self.project_dir / f"statistics_{now_string()}.txt"

    def ensure_project_dir(self) -> None:
        self.project_dir.mkdir(parents=True, exist_ok=True)


class LabelingPaths(ProjectPaths):
    @property
    def figures_path(self) -> Path:
        return self.project_dir / "figures.json"

    @property
    def review_path(self) -> Path:
        return self.project_dir / "review.json"

    @property
    def images_dir(self) -> Path:
        return self.project_dir / "images"

    @property
    def archive_path(self) -> Path:
        return self.project_dir / "archive.zip"


class FilteringPaths(ProjectPaths):
    @property
    def video_path(self) -> Path:
        return self.project_dir / "video.mp4"

    @property
    def selected_frames_path(self) -> Path:
        return self.project_dir / "selected_frames.json"
