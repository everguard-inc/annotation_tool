import json
import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from annotation_tool.core.exceptions import SettingsError


DEFAULT_SETTINGS: dict[str, dict[str, dict[str, Any]]] = {
    "general": {
        "token": {"type": "string", "value": None},
        "api_url": {"type": "string", "value": None},
        "file_url": {"type": "string", "value": None},
        "data_dir": {"type": "string", "value": None},
    },
    "interface": {
        "bbox_line_width": {"type": "number", "value": 3.0, "min": 1, "max": 10, "step": 1},
        "cursor_proximity_threshold": {"type": "number", "value": 3.0, "min": 1, "max": 10, "step": 1},
        "objects_opacity": {"type": "number", "value": 0.9, "min": 0, "max": 1, "step": 0.1},
        "color_fill_opacity": {"type": "number", "value": 0.1, "min": 0, "max": 1, "step": 0.1},
        "bbox_handler_size": {"type": "number", "value": 3.0, "min": 1, "max": 10, "step": 1},
        "keypoint_handler_size": {"type": "number", "value": 5.0, "min": 1, "max": 10, "step": 1},
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
        self._raw = deepcopy(DEFAULT_SETTINGS)

    def load(self) -> AppSettings:
        self._raw = self._load_raw()
        self._save_raw(self._raw)
        return self._to_settings(self._raw)

    def save(self, settings: AppSettings) -> None:
        self._raw["general"]["token"]["value"] = settings.token
        self._raw["general"]["api_url"]["value"] = settings.api_url
        self._raw["general"]["file_url"]["value"] = settings.file_url
        self._raw["general"]["data_dir"]["value"] = str(settings.data_dir)

        self._raw["interface"]["bbox_line_width"]["value"] = settings.bbox_line_width
        self._raw["interface"]["cursor_proximity_threshold"]["value"] = settings.cursor_proximity_threshold
        self._raw["interface"]["objects_opacity"]["value"] = settings.objects_opacity
        self._raw["interface"]["color_fill_opacity"]["value"] = settings.color_fill_opacity
        self._raw["interface"]["bbox_handler_size"]["value"] = settings.bbox_handler_size
        self._raw["interface"]["keypoint_handler_size"]["value"] = settings.keypoint_handler_size

        self._save_raw(self._raw)
        self._ensure_data_dir(settings.data_dir)

    def raw(self) -> dict[str, Any]:
        return deepcopy(self._raw)

    def has_empty_required_values(self) -> bool:
        raw = self._load_raw()
        for key in ("token", "api_url", "file_url", "data_dir"):
            value = raw["general"][key]["value"]
            if value is None or str(value).strip() == "":
                return True
        return False

    def _load_raw(self) -> dict[str, Any]:
        raw = deepcopy(DEFAULT_SETTINGS)

        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as file:
                user_raw = json.load(file)

            self._merge_existing_values(raw, user_raw)

        return raw

    def _merge_existing_values(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        for section_name, section in target.items():
            source_section = source.get(section_name, {})
            for key, setting in section.items():
                if key in source_section and "value" in source_section[key]:
                    setting["value"] = source_section[key]["value"]

    def _save_raw(self, raw: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(raw, file, indent=4)

        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def _to_settings(self, raw: dict[str, Any]) -> AppSettings:
        def value(section: str, name: str) -> Any:
            result = raw[section][name]["value"]
            if result is None or str(result).strip() == "":
                raise SettingsError(f"Specify `{name}` in Project > Settings.")
            return result

        data_dir = Path(value("general", "data_dir")).expanduser()
        self._ensure_data_dir(data_dir)

        return AppSettings(
            token=str(value("general", "token")),
            api_url=str(value("general", "api_url")).rstrip("/"),
            file_url=str(value("general", "file_url")).rstrip("/"),
            data_dir=data_dir,
            bbox_line_width=float(value("interface", "bbox_line_width")),
            cursor_proximity_threshold=float(value("interface", "cursor_proximity_threshold")),
            objects_opacity=float(value("interface", "objects_opacity")),
            color_fill_opacity=float(value("interface", "color_fill_opacity")),
            bbox_handler_size=float(value("interface", "bbox_handler_size")),
            keypoint_handler_size=float(value("interface", "keypoint_handler_size")),
        )

    def _ensure_data_dir(self, data_dir: Path) -> None:
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self._raw["general"]["data_dir"]["value"] = None
            self._save_raw(self._raw)
            raise SettingsError(f"Unable to create data_dir in '{data_dir}'.") from error
