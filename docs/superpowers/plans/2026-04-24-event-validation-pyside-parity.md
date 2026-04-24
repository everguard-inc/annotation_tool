# Event Validation PySide Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current PySide Event Validation deferral with functional parity for the Tk `EVENT_VALIDATION` workflow on Linux.

**Architecture:** Add Event Validation as a normal first-class PySide project mode using the existing layer split: paths/models/repository in `core/` and `infrastructure/`, workflow in `services/`, and all Qt widgets in `ui/`. Store PySide EV state in JSON (`cache.json`, `runtime_state.json`) while preserving read-only migration from Tk SQLite and export compatibility with `event_validation_results.json`.

**Tech Stack:** Python, PySide6, OpenCV, pytest with `QT_QPA_PLATFORM=offscreen`, existing `FileTransferClient`, `ArchiveUnzipper`, `SessionStateStore`, and `StatisticsService`.

---

## File Structure

- Create `annotation_tool/core/paths.py` additions: `EventValidationPaths` with `archive_path`, `videos_dir`, `images_dir`, and `results_path`.
- Create `annotation_tool/infrastructure/repositories/event_validation_repository.py`: load/save EV fields and events from `cache.json`, migrate from Tk SQLite `event` and `value.fields`, count incomplete events, and expose ordered event records.
- Modify `annotation_tool/services/import_export_service.py`: import EV archive/meta/results, build EV cache, overwrite EV annotations, and export `event_validation_results.json`.
- Create `annotation_tool/services/event_validation_session.py`: load event media, maintain answers/comment/view mode/current frame, persist state/statistics, and expose status.
- Create `annotation_tool/ui/widgets/status_bar_event_validation.py`: Qt status bar matching existing adaptive font behavior.
- Create `annotation_tool/ui/screens/event_validation_screen.py`: canvas + sidebar + video slider + keyboard controls.
- Modify `annotation_tool/ui/main_window.py`: route EV projects to `EventValidationScreen` instead of the deferral dialog.
- Modify or replace `tests/test_event_validation_deferral.py`: EV is no longer deferred; tests must assert routing/import/export behavior.

---

## Tk Source Evidence To Preserve

- Current PySide has three EV deferral sites plus one module constant to remove: `annotation_tool/ui/main_window.py` has `EVENT_VALIDATION_DEFERRAL_MESSAGE`, and EV guards in `open_project()`, `download_project()`, and `_set_project_screen()`.
- Tk EV SQLite schema comes from `origin/main:annotation_widgets/event_validation/models.py`: table `event`, columns `id`, `uid`, `comment`, and `custom_fields`; `custom_fields` stores JSON answers.
- Tk stores EV fields in the generic `value` table under name `fields`; `origin/main:annotation_widgets/event_validation/io.py` writes `Value.update_value("fields", json.dumps(fields_tree_data), overwrite=True)`.
- Tk EV meta file is `meta.json`; `origin/main:path_manager.py` exposes `meta_ann_path`, and `origin/main:annotation_widgets/event_validation/io.py` reads it as a list of `{"question", "answers", "colors"}` dictionaries.
- Tk EV archive layout is top-level `videos/` and optional `images/`; `origin/main:annotation_widgets/event_validation/path_manager.py` defines `videos_path = project_path/videos` and `images_path = project_path/images`, while `origin/main:annotation_widgets/event_validation/io.py` unzips `archive.zip` into `project_path` and then asserts/scans `videos_path`.
- Tk EV export shape is intentionally `{"fields": list(fields.keys()), "events": {...}}`; `origin/main:annotation_widgets/event_validation/io.py::_export_event_validation_results()` documents and writes `fields` as a bare ordered list of question names, not the answer/color map.
- `CompletionService` does not need a production-code change for EV stage progression: its current fallback in `_next_stage()` returns `DONE` for stages outside annotate/correction/review. The EV work should add regression coverage for this instead of changing service behavior unnecessarily.

---

### Task 1: Event Validation Paths And Repository

**Files:**
- Modify: `annotation_tool/core/paths.py`
- Create: `annotation_tool/infrastructure/repositories/event_validation_repository.py`
- Test: `tests/test_event_validation_repository.py`

- [ ] **Step 1: Write the failing repository tests**

```python
import json
import sqlite3
from pathlib import Path

from annotation_tool.core.paths import EventValidationPaths
from annotation_tool.infrastructure.repositories.event_validation_repository import (
    EventValidationRepository,
)


def test_event_validation_repository_migrates_tk_sqlite_cache(data_dir: Path) -> None:
    """Pins origin/main Tk schema:
    annotation_widgets/event_validation/models.py defines event.id,
    event.uid, event.comment, and event.custom_fields.
    models.Value supplies value.name/value.value for the fields payload.
    """
    paths = EventValidationPaths(data_dir, 42)
    paths.ensure_project_dir()
    conn = sqlite3.connect(paths.db_path)
    conn.execute("CREATE TABLE value (id INTEGER PRIMARY KEY, name TEXT, value TEXT)")
    conn.execute(
        "INSERT INTO value (name, value) VALUES (?, ?)",
        (
            "fields",
            json.dumps({"Status": {"TP": "green", "FP": "red"}}),
        ),
    )
    conn.execute(
        "CREATE TABLE event (id INTEGER PRIMARY KEY, uid TEXT, comment TEXT, custom_fields TEXT)"
    )
    conn.execute(
        "INSERT INTO event (uid, comment, custom_fields) VALUES (?, ?, ?)",
        ("ev-a", "checked", json.dumps(["TP"])),
    )
    conn.commit()
    conn.close()

    repository = EventValidationRepository(data_dir, 42)

    assert repository.fields() == {"Status": {"TP": "green", "FP": "red"}}
    assert repository.events()[0]["uid"] == "ev-a"
    assert repository.events()[0]["comment"] == "checked"
    assert repository.events()[0]["answers"] == ["TP"]
    assert paths.cache_path.exists()


def test_event_validation_repository_counts_incomplete_events(data_dir: Path) -> None:
    paths = EventValidationPaths(data_dir, 43)
    paths.ensure_project_dir()
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {
                    "ev-a": {"answers": ["TP"], "comment": ""},
                    "ev-b": {"answers": [""], "comment": ""},
                    "ev-c": {"answers": [], "comment": ""},
                },
            }
        ),
        encoding="utf-8",
    )

    repository = EventValidationRepository(data_dir, 43)

    assert repository.count_incomplete() == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_event_validation_repository.py
```

Expected: FAIL because `EventValidationPaths` and `EventValidationRepository` do not exist.

- [ ] **Step 3: Implement paths and repository**

Add to `annotation_tool/core/paths.py`:

```python
class EventValidationPaths(ProjectPaths):
    @property
    def archive_path(self) -> Path:
        return self.project_dir / "archive.zip"

    @property
    def videos_dir(self) -> Path:
        return self.project_dir / "videos"

    @property
    def images_dir(self) -> Path:
        return self.project_dir / "images"

    @property
    def results_path(self) -> Path:
        return self.project_dir / "event_validation_results.json"
```

Create `annotation_tool/infrastructure/repositories/event_validation_repository.py`:

```python
import json
import sqlite3
from pathlib import Path
from typing import Any

from annotation_tool.core.paths import EventValidationPaths
from annotation_tool.core.utils import read_json, write_json


class EventValidationRepository:
    def __init__(self, data_dir: Path, project_id: int) -> None:
        self.paths = EventValidationPaths(data_dir, project_id)

    def fields(self) -> dict[str, dict[str, str]]:
        return dict(self._cache().get("fields", {}))

    def events(self) -> list[dict[str, Any]]:
        events = self._cache().get("events", {})
        return [
            {"uid": uid, **dict(data)}
            for uid, data in sorted(events.items(), key=lambda item: item[0])
        ]

    def event(self, uid: str) -> dict[str, Any]:
        data = self._cache().get("events", {}).get(uid, {})
        return {
            "uid": uid,
            "answers": list(data.get("answers", [])),
            "comment": data.get("comment") or "",
        }

    def save_event(self, uid: str, answers: list[str], comment: str) -> None:
        cache = self._cache()
        cache.setdefault("events", {})[uid] = {
            "answers": list(answers),
            "comment": comment,
        }
        write_json(self.paths.cache_path, cache)

    def count_incomplete(self) -> int:
        count = 0
        for event in self.events():
            answers = event.get("answers", [])
            if not answers or any(str(answer).strip() == "" for answer in answers):
                count += 1
        return count

    def _cache(self) -> dict[str, Any]:
        if self.paths.cache_path.exists():
            return read_json(self.paths.cache_path)
        migrated = self._try_migrate_from_sqlite()
        if migrated is not None:
            write_json(self.paths.cache_path, migrated)
            return migrated
        return {"fields": {}, "events": {}}

    def _try_migrate_from_sqlite(self) -> dict[str, Any] | None:
        if not self.paths.db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(self.paths.db_path))
        except sqlite3.Error:
            return None
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "event" not in tables:
                return None
            fields = {}
            if "value" in tables:
                row = conn.execute(
                    "SELECT value FROM value WHERE name='fields'"
                ).fetchone()
                fields = json.loads(row[0]) if row and row[0] else {}
            rows = conn.execute(
                "SELECT uid, comment, custom_fields FROM event ORDER BY uid"
            ).fetchall()
        except (sqlite3.Error, json.JSONDecodeError):
            return None
        finally:
            conn.close()
        return {
            "fields": fields,
            "events": {
                uid: {
                    "answers": json.loads(custom_fields) if custom_fields else [],
                    "comment": comment or "",
                }
                for uid, comment, custom_fields in rows
            },
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_event_validation_repository.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add annotation_tool/core/paths.py annotation_tool/infrastructure/repositories/event_validation_repository.py tests/test_event_validation_repository.py
git commit -m "feat: add event validation repository"
```

---

### Task 2: Event Validation Import, Overwrite, And Export

**Files:**
- Modify: `annotation_tool/services/import_export_service.py`
- Test: `tests/test_event_validation_import_export.py`

- [ ] **Step 1: Write failing import/export tests**

```python
import json
from pathlib import Path

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import EventValidationPaths
from annotation_tool.core.utils import read_json
from annotation_tool.services.import_export_service import ImportExportService


class FakeTransfer:
    def __init__(self, files: dict[str, object]) -> None:
        self.files = files
        self.downloaded = []

    def download(self, uid, file_name, save_path, progress=None, ignore_404=False):
        self.downloaded.append(file_name)
        data = self.files.get(file_name)
        if data is None and ignore_404:
            return
        if isinstance(data, bytes):
            save_path.write_bytes(data)
        else:
            save_path.write_text(json.dumps(data), encoding="utf-8")

    def upload(self, uid, file_path):
        raise AssertionError("Upload not used in this test")


class FakeUnzipper:
    def unzip(self, archive_path: Path, output_dir: Path, progress=None):
        videos = output_dir / "videos"
        videos.mkdir(parents=True, exist_ok=True)
        (videos / "ev-a.mp4").write_bytes(b"fake")


def test_import_event_validation_project_builds_cache(data_dir: Path) -> None:
    """Pins Tk import shape:
    - archive.zip extracts into project root and provides top-level videos/
    - meta.json is a list of question/answers/colors dictionaries
    - prior results fields are a list of question names
    """
    project = ProjectData(
        id=44,
        uid="uid-44",
        stage=AnnotationStage.EVENT_VALIDATION,
        mode=AnnotationMode.EVENT_VALIDATION,
    )
    service = ImportExportService(
        data_dir,
        FakeTransfer(
            {
                "archive.zip": b"archive",
                "meta.json": [
                    {"question": "Status", "answers": ["TP", "FP"], "colors": ["green", "red"]}
                ],
                "event_validation_results.json": {
                    "fields": ["Status"],
                    "events": {"ev-a": {"answers": ["TP"], "comment": "ok"}},
                },
            }
        ),
        FakeUnzipper(),
    )

    service.import_project(project)

    cache = read_json(EventValidationPaths(data_dir, 44).cache_path)
    assert cache["fields"] == {"Status": {"TP": "green", "FP": "red"}}
    assert cache["events"]["ev-a"] == {"answers": ["TP"], "comment": "ok"}


def test_export_event_validation_results_writes_backend_shape(data_dir: Path) -> None:
    """Pins Tk export contract from EventValidationIO._export_event_validation_results:
    fields is list(fields.keys()), while answer/color mappings stay in meta/cache.
    """
    project = ProjectData(
        id=45,
        uid="uid-45",
        stage=AnnotationStage.EVENT_VALIDATION,
        mode=AnnotationMode.EVENT_VALIDATION,
    )
    paths = EventValidationPaths(data_dir, 45)
    paths.ensure_project_dir()
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {"ev-a": {"answers": ["FP"], "comment": "bad"}},
            }
        ),
        encoding="utf-8",
    )
    service = ImportExportService(data_dir, FakeTransfer({}))

    result = service.export_results(project)

    assert result == [paths.results_path]
    assert read_json(paths.results_path) == {
        "fields": ["Status"],
        "events": {"ev-a": {"answers": ["FP"], "comment": "bad"}},
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_event_validation_import_export.py
```

Expected: FAIL because EV import currently raises `UserVisibleError`.

- [ ] **Step 3: Implement EV import/export**

In `ImportExportService.import_project()`, replace the EV deferral with:

```python
if project.mode is AnnotationMode.EVENT_VALIDATION:
    self.import_event_validation_project(project, progress)
elif project.mode is AnnotationMode.FILTERING:
    self.import_filtering_project(project, progress)
else:
    self.import_labeling_project(project, progress)
```

Add methods:

```python
def import_event_validation_project(
    self, project: ProjectData, progress: ProgressCallback | None = None
) -> None:
    if project.uid is None:
        raise UserVisibleError("Project UID is missing.")
    paths = EventValidationPaths(self.data_dir, project.id)
    paths.ensure_project_dir()
    self.file_transfer.download(project.uid, paths.archive_path.name, paths.archive_path, progress=progress)
    self.file_transfer.download(project.uid, paths.meta_path.name, paths.meta_path, progress=progress)
    self.file_transfer.download(
        project.uid,
        paths.results_path.name,
        paths.results_path,
        progress=progress,
        ignore_404=True,
    )
    if not paths.videos_dir.exists():
        self.unzipper.unzip(paths.archive_path, paths.project_dir, progress=progress)
    self._build_event_validation_cache(paths)

def overwrite_event_validation_project(
    self, project: ProjectData, progress: ProgressCallback | None = None
) -> None:
    if project.uid is None:
        raise UserVisibleError("Project UID is missing.")
    paths = EventValidationPaths(self.data_dir, project.id)
    self.file_transfer.download(project.uid, paths.meta_path.name, paths.meta_path, progress=progress)
    self.file_transfer.download(
        project.uid,
        paths.results_path.name,
        paths.results_path,
        progress=progress,
        ignore_404=True,
    )
    self._build_event_validation_cache(paths)

def export_event_validation_results(self, project: ProjectData) -> Path:
    paths = EventValidationPaths(self.data_dir, project.id)
    cache = self._read_cache(paths.cache_path)
    result = {"fields": list(cache.get("fields", {}).keys()), "events": cache.get("events", {})}
    write_json(paths.results_path, result)
    return paths.results_path

def _build_event_validation_cache(self, paths: EventValidationPaths) -> None:
    meta = read_json(paths.meta_path)
    fields = {
        item["question"]: {
            answer: color
            for answer, color in zip(item.get("answers", []), item.get("colors", []))
        }
        for item in meta
    }
    imported = read_json(paths.results_path) if paths.results_path.exists() and is_valid_json(paths.results_path) else {}
    events = {}
    for video_path in sorted(paths.videos_dir.iterdir()):
        if not video_path.is_file():
            continue
        uid = video_path.stem
        imported_event = imported.get("events", {}).get(uid, {})
        events[uid] = {
            "answers": imported_event.get("answers", []),
            "comment": imported_event.get("comment") or "",
        }
    write_json(paths.cache_path, {"fields": fields, "events": events})
```

Update `overwrite_annotations()`:

```python
if project.mode is AnnotationMode.EVENT_VALIDATION:
    self.overwrite_event_validation_project(project, progress)
    return
```

Update `export_results()`:

```python
if project.mode is AnnotationMode.EVENT_VALIDATION:
    return [self.export_event_validation_results(project)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_event_validation_import_export.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add annotation_tool/services/import_export_service.py tests/test_event_validation_import_export.py
git commit -m "feat: import and export event validation projects"
```

---

### Task 3: Event Validation Session

**Files:**
- Create: `annotation_tool/services/event_validation_session.py`
- Test: `tests/test_event_validation_session.py`

- [ ] **Step 1: Write failing session tests**

```python
import json
from pathlib import Path

import cv2
import numpy as np

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import EventValidationPaths
from annotation_tool.infrastructure.repositories.event_validation_repository import (
    EventValidationRepository,
)
from annotation_tool.services.event_validation_session import EventValidationSession


def _write_video(path: Path) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (32, 24))
    assert writer.isOpened()
    for index in range(3):
        frame = np.full((24, 32, 3), index * 60, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def test_event_validation_session_updates_answers_comment_and_frame(data_dir: Path) -> None:
    paths = EventValidationPaths(data_dir, 46)
    paths.ensure_project_dir()
    paths.videos_dir.mkdir(parents=True)
    _write_video(paths.videos_dir / "ev-a.mp4")
    paths.cache_path.write_text(
        json.dumps(
            {
                "fields": {"Status": {"TP": "green", "FP": "red"}},
                "events": {"ev-a": {"answers": [""], "comment": ""}},
            }
        ),
        encoding="utf-8",
    )
    project = ProjectData(46, "uid-46", AnnotationStage.EVENT_VALIDATION, AnnotationMode.EVENT_VALIDATION)
    session = EventValidationSession(project, EventValidationRepository(data_dir, 46))

    session.cycle_answer("Status")
    session.update_comment("checked")
    session.video_forward()
    session.save_current_item()

    event = EventValidationRepository(data_dir, 46).event("ev-a")
    assert event["answers"] == ["TP"]
    assert event["comment"] == "checked"
    assert session.status().current_frame_number == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_event_validation_session.py
```

Expected: FAIL because `EventValidationSession` does not exist.

- [ ] **Step 3: Implement session**

Create `annotation_tool/services/event_validation_session.py` with dataclasses for status and methods matching the test:

```python
from collections import OrderedDict
from dataclasses import dataclass

import cv2
import numpy as np

from annotation_tool.core.enums import AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.infrastructure.repositories.event_validation_repository import (
    EventValidationRepository,
)
from annotation_tool.services.session_state import SessionState, SessionStateStore
from annotation_tool.services.statistics_service import StatisticsService


@dataclass
class EventValidationStatusData:
    item_id: int
    items_count: int
    duration_hours: float
    speed_per_hour: float
    processed_count: int
    view_mode: str
    number_of_frames: int
    current_frame_number: int


class EventValidationSession:
    def __init__(
        self,
        project: ProjectData,
        repository: EventValidationRepository,
        session_state_store: SessionStateStore | None = None,
        statistics_service: StatisticsService | None = None,
    ) -> None:
        self.project = project
        self.repository = repository
        self.session_state_store = session_state_store
        self.statistics_service = statistics_service
        self.event_uids = [event["uid"] for event in repository.events()]
        state = session_state_store.load() if session_state_store else SessionState(0, 0.0, set())
        self.item_id = min(state.item_id, max(len(self.event_uids) - 1, 0))
        self.duration_hours = state.duration_hours
        self.processed_item_ids = set(state.processed_item_ids)
        if self.statistics_service is not None:
            self.statistics_service.duration_hours = self.duration_hours
        self.fields = repository.fields()
        self.questions = list(self.fields.keys())
        self.answers = OrderedDict((question, "") for question in self.questions)
        self.comment = ""
        self.frames: list[np.ndarray] = []
        self.current_frame_number = 0
        self.view_mode = "VIDEO"
        self.load_current_item()

    def item_count(self) -> int:
        return len(self.event_uids)

    def current_item_id(self) -> int:
        return self.item_id

    def current_frame(self) -> np.ndarray:
        return self.frames[self.current_frame_number]

    def status(self) -> EventValidationStatusData:
        return EventValidationStatusData(
            item_id=self.item_id,
            items_count=max(self.item_count(), 1),
            duration_hours=self.duration_hours,
            speed_per_hour=round(len(self.processed_item_ids) / (self.duration_hours + 1e-7), 2),
            processed_count=len(self.processed_item_ids),
            view_mode=self.view_mode,
            number_of_frames=len(self.frames),
            current_frame_number=self.current_frame_number + 1,
        )

    def load_current_item(self) -> None:
        if not self.event_uids:
            return
        event = self.repository.event(self.event_uids[self.item_id])
        stored_answers = event.get("answers", [])
        self.answers = OrderedDict(
            (question, stored_answers[index] if index < len(stored_answers) else "")
            for index, question in enumerate(self.questions)
        )
        self.comment = event.get("comment", "")
        self._load_video_frames()

    def save_current_item(self) -> None:
        if not self.event_uids:
            return
        self.repository.save_event(
            self.event_uids[self.item_id],
            list(self.answers.values()),
            self.comment,
        )

    def go_to_item(self, item_id: int) -> None:
        if not self.event_uids:
            return
        self._track_action("keyboard")
        self.save_current_item()
        self.processed_item_ids.add(self.item_id)
        self.item_id = max(0, min(item_id, self.item_count() - 1))
        self.load_current_item()
        self._persist_state()

    def next_item(self) -> None:
        self.go_to_item(self.item_id + 1)

    def previous_item(self) -> None:
        self.go_to_item(self.item_id - 1)

    def update_comment(self, comment: str) -> None:
        self._track_action("keyboard")
        self.comment = comment

    def update_answer(self, question: str, answer: str) -> None:
        self._track_action("keyboard")
        self.answers[question] = answer

    def cycle_answer(self, question: str) -> None:
        options = list(self.fields[question].keys())
        current = self.answers.get(question, "")
        next_index = (options.index(current) + 1) % len(options) if current in options else 0
        self.update_answer(question, options[next_index])

    def video_forward(self) -> None:
        self._track_action("keyboard")
        self.current_frame_number = min(self.current_frame_number + 1, len(self.frames) - 1)

    def video_backward(self) -> None:
        self._track_action("keyboard")
        self.current_frame_number = max(self.current_frame_number - 1, 0)

    def close(self) -> None:
        self.save_current_item()
        self._persist_state()

    def _load_video_frames(self) -> None:
        self.frames = []
        path = self.repository.paths.videos_dir / f"{self.event_uids[self.item_id]}.mp4"
        cap = cv2.VideoCapture(str(path))
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            self.frames.append(frame)
        cap.release()
        self.current_frame_number = max(0, int(len(self.frames) / 2) - 1)

    def _track_action(self, message: str) -> None:
        if self.statistics_service is None:
            return
        self.duration_hours = self.statistics_service.track_action(
            AnnotationStage.EVENT_VALIDATION,
            message,
        )

    def _persist_state(self) -> None:
        if self.session_state_store is None:
            return
        self.session_state_store.save(
            SessionState(self.item_id, self.duration_hours, set(self.processed_item_ids))
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_event_validation_session.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add annotation_tool/services/event_validation_session.py tests/test_event_validation_session.py
git commit -m "feat: add event validation session"
```

---

### Task 4: PySide Event Validation UI And Routing

**Files:**
- Create: `annotation_tool/ui/widgets/status_bar_event_validation.py`
- Create: `annotation_tool/ui/screens/event_validation_screen.py`
- Modify: `annotation_tool/ui/main_window.py`
- Replace: `tests/test_event_validation_deferral.py`

- [ ] **Step 1: Write failing UI/routing tests**

```python
import inspect

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.ui import main_window
from annotation_tool.ui.main_window import MainWindow
from annotation_tool.ui.screens.event_validation_screen import EventValidationScreen


def test_main_window_has_no_event_validation_deferral_guards():
    source = inspect.getsource(main_window)

    assert "EVENT_VALIDATION_DEFERRAL_MESSAGE" not in source
    assert "Event validation not available" not in source
    assert "Please complete this project in the Tk build" not in source


def test_main_window_routes_event_validation_to_screen(qapp, valid_settings_file, monkeypatch):
    window = MainWindow.__new__(MainWindow)
    window.settings = object()
    window.current_screen = None
    window.current_project = None
    project = ProjectData(50, "uid-50", AnnotationStage.EVENT_VALIDATION, AnnotationMode.EVENT_VALIDATION)

    created = {}

    class FakePaths:
        runtime_state_path = "/tmp/runtime_state.json"
        db_path = "/tmp/db.sqlite"
        results_path = "/tmp/event_validation_results.json"

        def __init__(self, data_dir, project_id):
            created["paths"] = (data_dir, project_id)

    class FakeRepository:
        def __init__(self, data_dir, project_id):
            created["repository"] = (data_dir, project_id)

    class FakeSession:
        def __init__(self, project_data, repository, session_state_store, statistics_service=None):
            created["session_project"] = project_data

    class FakeScreen:
        def __init__(self, session, results_path, parent=None):
            created["screen"] = (session, results_path, parent)

    monkeypatch.setattr("annotation_tool.ui.main_window.EventValidationPaths", FakePaths)
    monkeypatch.setattr("annotation_tool.ui.main_window.EventValidationRepository", FakeRepository)
    monkeypatch.setattr("annotation_tool.ui.main_window.EventValidationSession", FakeSession)
    monkeypatch.setattr("annotation_tool.ui.main_window.EventValidationScreen", FakeScreen)
    monkeypatch.setattr("annotation_tool.ui.main_window.SessionStateStore", lambda *args, **kwargs: object())
    monkeypatch.setattr("annotation_tool.ui.main_window.StatisticsService", lambda *args, **kwargs: object())
    monkeypatch.setattr(window, "setCentralWidget", lambda screen: created.setdefault("central", screen))
    monkeypatch.setattr(window, "set_current_project_title", lambda project_id: created.setdefault("title", project_id))

    window._set_project_screen(project)

    assert created["session_project"] == project
    assert created["title"] == 50


def test_event_validation_screen_exports_results(tmp_path):
    class FakeSession:
        duration_hours = 0.0
        def item_count(self): return 1
        def close(self): pass
        def save_current_item(self): self.saved = True

    screen = EventValidationScreen.__new__(EventValidationScreen)
    screen.session = FakeSession()
    screen.results_path = tmp_path / "event_validation_results.json"

    assert screen.export_results() == [screen.results_path]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_event_validation_deferral.py
```

Expected: FAIL because `EventValidationScreen` does not exist and routing blocks EV.

- [ ] **Step 3: Implement screen and route**

Create `status_bar_event_validation.py` by mirroring `FilteringStatusBar` with labels for mode, item id, speed, position, duration, preview mode, and frame.

Create `event_validation_screen.py` with:

```python
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QComboBox, QLabel, QPushButton, QSlider, QTextEdit, QVBoxLayout, QWidget

from annotation_tool.media.image_converter import numpy_to_qimage
from annotation_tool.services.event_validation_session import EventValidationSession
from annotation_tool.ui.screens.base_screen import BaseProjectScreen
from annotation_tool.ui.widgets.image_canvas import ImageCanvas
from annotation_tool.ui.widgets.status_bar_event_validation import EventValidationStatusBar


class EventValidationScreen(BaseProjectScreen):
    def __init__(self, session: EventValidationSession, results_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.results_path = results_path
        self.canvas = ImageCanvas(self)
        self.status_bar = EventValidationStatusBar(self)
        self.sidebar = QWidget(self)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.comment_input = QTextEdit(self.sidebar)
        self.answer_inputs = {}
        self.slider = QSlider(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.slider)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.status_bar)
        self.canvas.key_pressed.connect(self.handle_key_press)
        self._build_sidebar()
        QTimer.singleShot(0, lambda: self.refresh(fit=True))

    @property
    def items_count(self) -> int:
        return self.session.item_count()

    @property
    def duration_hours(self) -> float:
        return self.session.duration_hours

    def save(self) -> None:
        self.session.save_current_item()

    def close_screen(self) -> None:
        self.session.close()

    def go_to_id(self, item_id: int) -> None:
        self.session.go_to_item(item_id)
        self._build_sidebar()
        self.refresh(fit=True)

    def export_results(self) -> list[Path]:
        self.session.save_current_item()
        return [self.results_path]

    def should_remove_after_completion(self) -> bool:
        return True

    def refresh(self, fit: bool = False) -> None:
        self.canvas.set_image(numpy_to_qimage(self.session.current_frame()))
        if fit:
            self.canvas.fit_image()
        self.status_bar.update_status(self.session.status())

    def handle_key_press(self, key: str) -> None:
        if key in {"w", "p"}:
            self.session.next_item()
            self._build_sidebar()
        elif key in {"q", "o"}:
            self.session.previous_item()
            self._build_sidebar()
        elif key == "x":
            self.session.video_forward()
        elif key == "z":
            self.session.video_backward()
        elif key.isdigit() and int(key) <= len(self.session.questions):
            self.session.cycle_answer(self.session.questions[int(key) - 1])
            self._build_sidebar()
        self.refresh(fit=True)

    def _build_sidebar(self) -> None:
        while self.sidebar_layout.count():
            item = self.sidebar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.answer_inputs = {}
        for question in self.session.questions:
            self.sidebar_layout.addWidget(QLabel(question, self.sidebar))
            combo = QComboBox(self.sidebar)
            combo.addItems([""] + list(self.session.fields[question].keys()))
            combo.setCurrentText(self.session.answers.get(question, ""))
            combo.currentTextChanged.connect(
                lambda value, q=question: self.session.update_answer(q, value)
            )
            self.answer_inputs[question] = combo
            self.sidebar_layout.addWidget(combo)
        self.comment_input = QTextEdit(self.sidebar)
        self.comment_input.setPlainText(self.session.comment)
        self.comment_input.textChanged.connect(
            lambda: self.session.update_comment(self.comment_input.toPlainText().strip())
        )
        self.sidebar_layout.addWidget(self.comment_input)
```

Modify `MainWindow._set_project_screen()` to instantiate `EventValidationRepository`, `EventValidationSession`, `SessionStateStore`, `StatisticsService`, and `EventValidationScreen` for `AnnotationMode.EVENT_VALIDATION`.

Make the EV classes patchable by tests: import `EventValidationPaths`, `EventValidationRepository`, `EventValidationSession`, `EventValidationScreen`, `SessionStateStore`, and `StatisticsService` at `annotation_tool/ui/main_window.py` module scope instead of only as function-local imports.

Remove all current deferral code from `annotation_tool/ui/main_window.py`:
- Delete the module-level `EVENT_VALIDATION_DEFERRAL_MESSAGE` constant.
- Delete the EV guard in `open_project()` that shows `"Event validation not available"`.
- Delete the EV guard in `download_project()` that shows `"Event validation not available"`.
- Replace the EV guard at the top of `_set_project_screen()` with real EV screen construction.

- [ ] **Step 4: Run UI tests**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_event_validation_deferral.py tests/test_menu_wiring.py tests/test_main_window.py
```

Expected: PASS after replacing deferral assertions with EV route assertions.

- [ ] **Step 5: Commit**

```bash
git add annotation_tool/ui/widgets/status_bar_event_validation.py annotation_tool/ui/screens/event_validation_screen.py annotation_tool/ui/main_window.py tests/test_event_validation_deferral.py
git commit -m "feat: route event validation to pyside screen"
```

---

### Task 5: Event Validation Completion Regression

**Files:**
- Modify: `tests/test_project_completion.py`

- [ ] **Step 1: Add EV completion coverage**

Add this case to `tests/test_project_completion.py::test_completion_service_changes_stage_and_calls_backend`:

```python
(
    AnnotationStage.EVENT_VALIDATION,
    AnnotationMode.EVENT_VALIDATION,
    AnnotationStage.DONE,
),
```

If the existing parametrization only accepts `(initial_stage, expected_stage)`, change it to `(initial_stage, mode, expected_stage)` and pass `mode=mode` into `ProjectData`.

- [ ] **Step 2: Run the completion test**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_project_completion.py::test_completion_service_changes_stage_and_calls_backend
```

Expected: PASS. This should pass without modifying `annotation_tool/services/completion_service.py`, because `_next_stage()` already returns `DONE` for non-labeling terminal workflows. If it fails, make the smallest explicit `_next_stage()` change for `AnnotationStage.EVENT_VALIDATION -> AnnotationStage.DONE` and rerun the same test.

- [ ] **Step 3: Commit**

```bash
git add tests/test_project_completion.py annotation_tool/services/completion_service.py
git commit -m "test: pin event validation completion stage"
```

If `completion_service.py` did not change, use:

```bash
git add tests/test_project_completion.py
git commit -m "test: pin event validation completion stage"
```

---

### Task 6: Docs And Full Verification

**Files:**
- Modify: `docs/quality/pyside-release-readiness-2026-04-23.md`
- Modify: `docs/quality/pyside-test-disposition.md`
- Modify: `docs/quality/branch-audit-origin-main-vs-pyside-2026-04-23.html`
- Test: full suite

- [ ] **Step 1: Update docs**

Remove the EV deferral language from the readiness verdict and replace it with:

```markdown
### Event validation

Event validation is now in PySide first-release scope on Linux.

Covered behavior:
- EV project download/import from archive, meta, and prior results
- EV answers/comment persistence in PySide cache
- EV export to `event_validation_results.json`
- EV completion upload via the existing completion service
- EV screen routing from the main project shell

macOS remains out of scope.
```

- [ ] **Step 2: Run full verification**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
PYTHONPATH=. venv/bin/python -m compileall -q annotation_tool tests
git diff --check
```

Expected:
- pytest reports all tests passing
- compileall exits 0
- diff check exits 0

- [ ] **Step 3: Commit docs**

```bash
git add docs/quality/pyside-release-readiness-2026-04-23.md docs/quality/pyside-test-disposition.md docs/quality/branch-audit-origin-main-vs-pyside-2026-04-23.html
git commit -m "docs: mark event validation in pyside scope"
```

---

## Self-Review

Spec coverage:
- Replaces EV deferral with repository, import/export, session, UI, completion, docs, and tests.
- Keeps macOS out of scope.
- Preserves layer boundaries from `AGENTS.md`.

Placeholder scan:
- No `TBD`, `TODO`, or unspecified edge handling remains in task steps.

Type consistency:
- `EventValidationPaths`, `EventValidationRepository`, `EventValidationSession`, and `EventValidationScreen` are named consistently across tasks.
