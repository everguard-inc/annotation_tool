from pathlib import Path
from typing import Callable

ProgressCallback = Callable[[float, float, float, float], None]


class FileTransferClient:
    def __init__(self, file_url: str, token: str) -> None:
        ...

    def download(
        self,
        uid: str,
        file_name: str,
        save_path: Path,
        progress: ProgressCallback | None = None,
        ignore_404: bool = False,
    ) -> None:
        ...

    def upload(self, uid: str, file_path: Path) -> None:
        ...
