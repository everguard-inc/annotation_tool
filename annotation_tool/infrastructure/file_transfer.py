from pathlib import Path
from typing import Callable

import requests

from annotation_tool.core.exceptions import BackendError

ProgressCallback = Callable[[float, float, float, float], None]
CancelCallback = Callable[[], bool]


class FileTransferClient:
    def __init__(self, file_url: str, token: str, timeout_seconds: int = 30) -> None:
        self.file_url = file_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    def download(
        self,
        uid: str,
        file_name: str,
        save_path: Path,
        progress: ProgressCallback | None = None,
        should_cancel: CancelCallback | None = None,
        ignore_404: bool = False,
    ) -> None:
        save_path.parent.mkdir(parents=True, exist_ok=True)

        url = f"{self.file_url}/download/{uid}/{file_name}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            with requests.post(url, headers=headers, stream=True, timeout=self.timeout_seconds) as response:
                if response.status_code == 404 and ignore_404:
                    return

                if response.status_code != 200:
                    raise BackendError(self._error_message(response, f"Unable to download file {uid}/{file_name}."))

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                import time

                started_at = time.time()

                with save_path.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if should_cancel is not None and should_cancel():
                            return

                        if not chunk:
                            continue

                        file.write(chunk)
                        downloaded += len(chunk)

                        if progress is not None:
                            elapsed = max(time.time() - started_at, 1e-7)
                            speed_mbps = downloaded / elapsed / 1024 / 1024
                            remaining = (total_size - downloaded) / max(downloaded / elapsed, 1e-7) if total_size else 0
                            percent = downloaded / total_size * 100 if total_size else 0
                            progress(percent, downloaded / 1024 / 1024 / 1024, speed_mbps, remaining)

                if progress is not None:
                    progress(100, downloaded / 1024 / 1024 / 1024, 0, 0)
        except requests.RequestException as error:
            raise BackendError(f"Unable to download file {uid}/{file_name}: {error}") from error

    def upload(self, uid: str, file_path: Path) -> None:
        if not file_path.exists():
            raise BackendError(f"File does not exist: {file_path}")

        url = f"{self.file_url}/upload/{uid}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            with file_path.open("rb") as file:
                response = requests.post(url, files={"file": file}, headers=headers, timeout=self.timeout_seconds)
        except requests.RequestException as error:
            raise BackendError(f"Unable to upload file {file_path}: {error}") from error

        if response.status_code != 200:
            raise BackendError(self._error_message(response, f"Unable to upload file {file_path}."))

    def _error_message(self, response: requests.Response, prefix: str) -> str:
        try:
            body = response.json()
        except ValueError:
            body = response.text
        return f"{prefix} Status code: {response.status_code}. {body}"
