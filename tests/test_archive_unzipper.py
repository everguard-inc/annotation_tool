import zipfile
from pathlib import Path

from annotation_tool.infrastructure.unzip import ArchiveUnzipper


def test_unzip_extracts_archive_and_reports_progress(tmp_path: Path) -> None:
    """Covers FR-007, FR-172, FR-173."""
    archive_path = tmp_path / "archive.zip"
    output_dir = tmp_path / "images"
    progress_values = []

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("a.txt", "hello")
        archive.writestr("b.txt", "world")

    ArchiveUnzipper().unzip(
        archive_path=archive_path,
        output_dir=output_dir,
        progress=lambda percent, *_: progress_values.append(percent),
    )

    assert (output_dir / "a.txt").read_text(encoding="utf-8") == "hello"
    assert (output_dir / "b.txt").read_text(encoding="utf-8") == "world"
    assert progress_values[-1] == 100
