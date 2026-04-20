import time
import zipfile
from pathlib import Path

from annotation_tool.core.exceptions import UserVisibleError
from annotation_tool.infrastructure.file_transfer import CancelCallback, ProgressCallback


class ArchiveUnzipper:
    def unzip(
        self,
        archive_path: Path,
        output_dir: Path,
        progress: ProgressCallback | None = None,
        should_cancel: CancelCallback | None = None,
    ) -> None:
        if not archive_path.exists():
            raise UserVisibleError(f"Archive not found: {archive_path}")

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                names = archive.namelist()
                total_size = sum(archive.getinfo(name).file_size for name in names)
                processed = 0
                started_at = time.time()

                for name in names:
                    if should_cancel is not None and should_cancel():
                        return

                    archive.extract(name, output_dir)
                    processed += archive.getinfo(name).file_size

                    if progress is not None:
                        elapsed = max(time.time() - started_at, 1e-7)
                        speed_mbps = processed / elapsed / 1024 / 1024
                        remaining = (total_size - processed) / max(processed / elapsed, 1e-7) if total_size else 0
                        percent = processed / total_size * 100 if total_size else 0
                        progress(percent, processed / 1024 / 1024 / 1024, speed_mbps, remaining)

                if progress is not None:
                    progress(100, processed / 1024 / 1024 / 1024, 0, 0)
        except zipfile.BadZipFile as error:
            raise UserVisibleError(f"Archive is corrupted: {archive_path}") from error
