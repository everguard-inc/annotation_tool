from dataclasses import dataclass
from pathlib import Path
from typing import Any

from annotation_tool.core.exceptions import SettingsError
from annotation_tool.core.utils import read_json, write_json


DEFAULT_SETTINGS = {
    "general": {
        "token": {"type": "string", "value": ""},
        "api_url": {"type": "string", "value": ""},
        "file_url": {"type": "string", "value": ""},
        "data_dir": {"type": "string", "value": ""},
    },
    "interface": {
        "bbox_line_width": {"type": "number", "value": 3.0},
        "cursor_proximity_threshold": {"type": "number", "value": 3.0},
        "objects_opacity": {"type": "number", "value": 0.9},
        "color_fill_opacity": {"type": "number", "value": 0.1},
        "bbox_handler_size": {"type": "number", "value": 3.0},
        "keypoint_handler_size": {"type": "number", "value": 5.0},
    },
}


@dataclass
class AppSettings:
    token: str
    api_url: str
    file_url: str
    data_dir: Path
    bbox_line_width: float
    cursor_proximity_threshold: float
    objects_opacity: float
    color_fill_opacity: float
    bbox_handler_size: float
    keypoint_handler_size: float


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.ensure_exists()

    def ensure_exists(self) -> None:
        if not self.path.exists():
            write_json(self.path, DEFAULT_SETTINGS)

    def load(self) -> AppSettings:
        data = self._merged_data()

        token = self._value(data, "general", "token")
        api_url = self._value(data, "general", "api_url").rstrip("/")
        file_url = self._value(data, "general", "file_url").rstrip("/")
        data_dir_raw = self._value(data, "general", "data_dir")

        missing = self.missing_required_values(data)
        if missing:
            raise SettingsError(f"Missing required settings: {', '.join(missing)}")

        data_dir = Path(data_dir_raw).expanduser()
        data_dir.mkdir(parents=True, exist_ok=True)

        return AppSettings(
            token=token,
            api_url=api_url,
            file_url=file_url,
            data_dir=data_dir,
            bbox_line_width=float(self._value(data, "interface", "bbox_line_width")),
            cursor_proximity_threshold=float(self._value(data, "interface", "cursor_proximity_threshold")),
            objects_opacity=float(self._value(data, "interface", "objects_opacity")),
            color_fill_opacity=float(self._value(data, "interface", "color_fill_opacity")),
            bbox_handler_size=float(self._value(data, "interface", "bbox_handler_size")),
            keypoint_handler_size=float(self._value(data, "interface", "keypoint_handler_size")),
        )

    def save(self, settings: AppSettings) -> None:
        data = self._merged_data()

        data["general"]["token"]["value"] = settings.token.strip()
        data["general"]["api_url"]["value"] = settings.api_url.strip().rstrip("/")
        data["general"]["file_url"]["value"] = settings.file_url.strip().rstrip("/")
        data["general"]["data_dir"]["value"] = str(settings.data_dir).strip()

        data["interface"]["bbox_line_width"]["value"] = settings.bbox_line_width
        data["interface"]["cursor_proximity_threshold"]["value"] = settings.cursor_proximity_threshold
        data["interface"]["objects_opacity"]["value"] = settings.objects_opacity
        data["interface"]["color_fill_opacity"]["value"] = settings.color_fill_opacity
        data["interface"]["bbox_handler_size"]["value"] = settings.bbox_handler_size
        data["interface"]["keypoint_handler_size"]["value"] = settings.keypoint_handler_size

        write_json(self.path, data)
        self.path.chmod(0o600)

    def has_empty_required_values(self) -> bool:
        return bool(self.missing_required_values(self._merged_data()))

    def missing_required_values(self, data: dict[str, Any] | None = None) -> list[str]:
        data = data or self._merged_data()
        required = ["token", "api_url", "file_url", "data_dir"]

        return [
            name
            for name in required
            if not str(self._value(data, "general", name)).strip()
        ]

    def draft_settings(self) -> AppSettings:
        data = self._merged_data()

        return AppSettings(
            token=str(self._value(data, "general", "token")),
            api_url=str(self._value(data, "general", "api_url")),
            file_url=str(self._value(data, "general", "file_url")),
            data_dir=Path(str(self._value(data, "general", "data_dir")) or str(Path.home() / "annotation")),
            bbox_line_width=float(self._value(data, "interface", "bbox_line_width")),
            cursor_proximity_threshold=float(self._value(data, "interface", "cursor_proximity_threshold")),
            objects_opacity=float(self._value(data, "interface", "objects_opacity")),
            color_fill_opacity=float(self._value(data, "interface", "color_fill_opacity")),
            bbox_handler_size=float(self._value(data, "interface", "bbox_handler_size")),
            keypoint_handler_size=float(self._value(data, "interface", "keypoint_handler_size")),
        )

    def _merged_data(self) -> dict[str, Any]:
        self.ensure_exists()
        data = read_json(self.path)
        return self._merge(DEFAULT_SETTINGS, data)

    def _merge(self, default: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        result = {}

        for key, value in default.items():
            if isinstance(value, dict) and key in user and isinstance(user[key], dict):
                result[key] = self._merge(value, user[key])
            else:
                result[key] = user.get(key, value)

        return result

    def _value(self, data: dict[str, Any], section: str, name: str) -> Any:
        item = data[section][name]
        return item["value"] if isinstance(item, dict) else item