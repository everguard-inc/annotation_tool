from pathlib import Path


class ProjectPaths:
    def __init__(self, data_dir: Path, project_id: int) -> None:
        ...

    @property
    def project_dir(self) -> Path:
        ...

    @property
    def db_path(self) -> Path:
        ...

    @property
    def state_path(self) -> Path:
        ...

    @property
    def meta_path(self) -> Path:
        ...

    @property
    def statistics_path(self) -> Path:
        ...


class LabelingPaths(ProjectPaths):
    @property
    def figures_path(self) -> Path:
        ...

    @property
    def review_path(self) -> Path:
        ...

    @property
    def images_dir(self) -> Path:
        ...

    @property
    def archive_path(self) -> Path:
        ...


class FilteringPaths(ProjectPaths):
    @property
    def video_path(self) -> Path:
        ...

    @property
    def selected_frames_path(self) -> Path:
        ...
