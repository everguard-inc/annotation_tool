from pathlib import Path

from annotation_tool.infrastructure.file_transfer import FileTransferClient


class FakeResponse:
    def __init__(self, status_code: int, body: bytes = b"", payload=None) -> None:
        self.status_code = status_code
        self.body = body
        self.payload = payload or {}
        self.text = str(self.payload)
        self.headers = {"content-length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def iter_content(self, chunk_size: int):
        yield self.body

    def json(self):
        return self.payload


def test_download_upload_and_optional_404_are_handled(tmp_path: Path, monkeypatch) -> None:
    """Covers FR-168, FR-169, FR-170, FR-171."""
    calls = []
    progress_values = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))

        if "/download/uid/missing.json" in url:
            return FakeResponse(404, payload={"error": "not found"})

        if "/download/uid/file.txt" in url:
            return FakeResponse(200, body=b"abc")

        if "/upload/uid" in url:
            return FakeResponse(200)

        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("annotation_tool.infrastructure.file_transfer.requests.post", fake_post)

    client = FileTransferClient("https://files.example.com", "token")
    downloaded_path = tmp_path / "file.txt"
    missing_path = tmp_path / "missing.json"

    client.download(
        uid="uid",
        file_name="file.txt",
        save_path=downloaded_path,
        progress=lambda percent, *_: progress_values.append(percent),
    )
    client.download(uid="uid", file_name="missing.json", save_path=missing_path, ignore_404=True)
    client.upload(uid="uid", file_path=downloaded_path)

    assert downloaded_path.read_bytes() == b"abc"
    assert not missing_path.exists()
    assert progress_values[-1] == 100
    assert calls[0][1]["headers"] == {"Authorization": "Bearer token"}
