import json
import os
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def valid_settings_file(tmp_path: Path) -> Path:
    data_dir = tmp_path / "annotation-data"
    settings_path = tmp_path / "settings.json"

    settings_path.write_text(
        json.dumps(
            {
                "general": {
                    "token": {"type": "string", "value": "token-123"},
                    "api_url": {"type": "string", "value": "https://api.example.com"},
                    "file_url": {"type": "string", "value": "https://files.example.com"},
                    "data_dir": {"type": "string", "value": str(data_dir)},
                },
                "interface": {
                    "bbox_line_width": {"type": "number", "value": 4.0},
                    "cursor_proximity_threshold": {"type": "number", "value": 5.0},
                    "objects_opacity": {"type": "number", "value": 0.8},
                    "color_fill_opacity": {"type": "number", "value": 0.2},
                    "bbox_handler_size": {"type": "number", "value": 6.0},
                    "keypoint_handler_size": {"type": "number", "value": 7.0},
                },
            }
        ),
        encoding="utf-8",
    )

    return settings_path
