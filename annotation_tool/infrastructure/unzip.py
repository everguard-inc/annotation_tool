from pathlib import Path
from annotation_tool.infrastructure.file_transfer import ProgressCallback


class ArchiveUnzipper:
    def unzip(
        self,
        archive_path: Path,
        output_dir: Path,
        progress: ProgressCallback | None = None,
    ) -> None:
        ...
