# Golden Parity Scenarios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact golden parity test lane that pins Tk workflow contracts through PySide production paths.

**Architecture:** Keep the tests PySide-native and deterministic, but derive expected contracts from `origin/main` Tk code. Add test helpers that simulate backend/file-transfer boundaries and assert side effects at the same points Tk produced them: imported local state, screen/session actions, completion upload lists, counter reset, project removal, overwrite refresh, and live settings application.

**Tech Stack:** Python, pytest, PySide6 offscreen, existing `tests/tk_era_fixture.py`, existing PySide services/screens/repositories.

---

## File Structure

- Create: `tests/test_golden_parity_labeling_completion.py`
  - Production-path completion tests for annotate/correction/review labeling projects.
- Create: `tests/test_golden_parity_overwrite_and_settings.py`
  - Production-path overwrite refresh and live settings propagation tests.
- Create: `tests/test_golden_parity_tk_migration.py`
  - Tk-era local project open tests that drive migrators through `MainWindow._set_project_screen`.
- Modify: `tests/tk_era_fixture.py`
  - Add image-file creation and state override support so Tk-era directories can be opened by real PySide sessions.
- Modify: `tests/conftest.py`
  - Reuse `create_pattern_image` from golden tests if needed.
- Likely modify: `annotation_tool/ui/main_window.py`
  - Add a completion close path that does not persist old runtime state after completion.
  - Add active-screen settings application after `Project > Settings`.
- Likely modify: `annotation_tool/ui/screens/labeling_screen.py`
  - Add `apply_annotation_style(style)` or equivalent.
- Likely modify: `annotation_tool/services/labeling_session.py`
  - Add `apply_annotation_style(style)` and update the current controller.

## Baseline Rule

Before executing code changes, refresh or verify the local Tk reference:

```bash
git fetch origin main pyside pyside-test
git rev-parse origin/main
git show origin/main:main.py >/tmp/tk-main.py
git show origin/main:annotation_widgets/io.py >/tmp/tk-io.py
git show origin/main:annotation_widgets/image/labeling/io.py >/tmp/tk-labeling-io.py
git show origin/main:annotation_widgets/widget.py >/tmp/tk-widget.py
```

Expected: `origin/main` resolves, and the files contain the Tk contracts used below:

- `main.py:complete_project` calls widget completion, then removes widget.
- `annotation_widgets/io.py:complete_annotation` uploads statistics/result files, calls backend completion, resets counters, updates stage, removes files when mode-specific rules say so.
- `annotation_widgets/image/labeling/io.py:_upload_annotation_results` uploads only `figures.json` in `ANNOTATE`/`CORRECTION`, only `review.json` in `REVIEW`.
- `annotation_widgets/widget.py:close` saves item only.

Always record the resolved `git rev-parse origin/main` SHA in the golden test module docstring or in this plan before implementing the tests. This is required even when `git fetch` succeeds, because `origin/main` is movable and future readers need the exact Tk contract revision encoded by the golden lane.

Current pinned Tk baseline for this plan revision: `origin/main` at `1dd11801066386f137f64ab2ad028005f325f463` from the local remote-tracking ref on 2026-04-24.

If network fetch is unavailable, use the already-present `origin/main` commit and explicitly note that the SHA came from the local remote-tracking ref.

---

### Task 1: Tk-Era Fixture Openability

**Files:**
- Modify: `tests/tk_era_fixture.py`
- Test: `tests/test_golden_parity_tk_migration.py`

- [ ] **Step 1: Write failing test for opening a Tk-era labeling project through PySide screen construction**

Create `tests/test_golden_parity_tk_migration.py`:

```python
"""Golden Tk parity tests.

Tk baseline: origin/main 1dd11801066386f137f64ab2ad028005f325f463.
"""

from pathlib import Path

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.settings import SettingsStore
from annotation_tool.ui.main_window import MainWindow
from annotation_tool.ui.screens.labeling_screen import LabelingScreen
from tests.tk_era_fixture import create_tk_era_labeling_project_dir


def test_tk_era_labeling_project_opens_through_pyside_main_window(
    qapp,
    valid_settings_file: Path,
) -> None:
    settings = SettingsStore(valid_settings_file).load()
    create_tk_era_labeling_project_dir(
        settings.data_dir,
        project_id=501,
        uid="tk-501",
        item_id=0,
        labels=[
            {"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"},
            {"name": "Fix", "color": "yellow", "hotkey": "1", "type": "REVIEW_LABEL"},
        ],
        images=[
            {
                "name": "a.jpg",
                "height": 20,
                "width": 30,
                "bboxes": [{"x1": 2, "y1": 3, "x2": 10, "y2": 12, "label": "car"}],
                "review_labels": [{"x": 5, "y": 6, "label": "Fix"}],
            }
        ],
        create_images=True,
    )
    window = MainWindow(SettingsStore(valid_settings_file))
    project = ProjectData(
        id=501,
        uid="tk-501",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )

    window._set_project_screen(project)

    assert isinstance(window.current_screen, LabelingScreen)
    assert window.current_screen.session.item_count() == 1
    assert window.current_screen.session.controller.figures()[0].label == "car"
    assert window.current_screen.session.review_figures[0].label == "Fix"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_golden_parity_tk_migration.py::test_tk_era_labeling_project_opens_through_pyside_main_window
```

Expected before fixture support: FAIL with `TypeError: create_tk_era_labeling_project_dir() got an unexpected keyword argument 'create_images'`.

- [ ] **Step 3: Extend Tk-era fixture with image creation**

In `tests/tk_era_fixture.py`, update the function signature:

```python
def create_tk_era_labeling_project_dir(
    data_dir: Path,
    project_id: int = 42,
    uid: str = "tk-era-labeling",
    item_id: int = 3,
    duration_hours: float = 1.25,
    processed_item_ids: list[int] | None = None,
    labels: list[dict] | None = None,
    images: list[dict] | None = None,
    stage: str = "ANNOTATE",
    mode: str = "OBJECT_DETECTION",
    create_images: bool = False,
) -> Path:
```

Replace the existing `_write_state_json(...)` call in that function with:

```python
    _write_state_json(project_dir, project_id, uid, stage, mode)
```

After `project_dir.mkdir(...)`, add:

```python
    if create_images:
        from tests.conftest import create_pattern_image

        images_dir = project_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        for image in image_rows:
            create_pattern_image(
                images_dir / image["name"],
                size=(image["width"], image["height"]),
                base=(240, 240, 240),
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_golden_parity_tk_migration.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/tk_era_fixture.py tests/test_golden_parity_tk_migration.py
git commit -m "test: add golden tk-era labeling open parity"
```

---

### Task 2: Labeling Completion Golden Contract

**Files:**
- Create: `tests/test_golden_parity_labeling_completion.py`
- Likely modify: `annotation_tool/ui/main_window.py`
- Likely modify: `annotation_tool/services/completion_service.py`

- [ ] **Step 1: Write failing test for completion upload/reset/removal through `MainWindow.complete_project`**

Create `tests/test_golden_parity_labeling_completion.py`:

```python
"""Golden labeling completion parity tests.

Tk baseline: origin/main 1dd11801066386f137f64ab2ad028005f325f463.
"""

from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import LabelingPaths, ProjectPaths
from annotation_tool.core.settings import SettingsStore
from annotation_tool.core.utils import read_json, write_json
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.services.completion_service import CompletionService
from annotation_tool.services.import_export_service import ImportExportService
from annotation_tool.ui import main_window as main_window_module
from annotation_tool.ui.main_window import MainWindow


class AvailableApi:
    def __init__(self) -> None:
        self.completed = []

    def is_available(self) -> bool:
        return True

    def complete_task(self, project_uid: str, duration_hours: float) -> None:
        self.completed.append((project_uid, duration_hours))


class RecordingTransfer:
    def __init__(self) -> None:
        self.uploaded = []

    def download(self, *args, **kwargs):
        raise AssertionError("download is not expected")

    def upload(self, uid: str, file_path: Path) -> None:
        self.uploaded.append((uid, file_path.name))


class CompletedScreen:
    items_count = 1

    def __init__(self) -> None:
        self.duration_hours = 2.5
        self.saved = 0
        self.closed = 0

    def save(self) -> None:
        self.saved += 1

    def close_screen(self) -> None:
        self.closed += 1
        raise AssertionError("completion close must not call normal close_screen")

    def deleteLater(self) -> None:
        pass

    def export_results(self) -> list[Path]:
        return []

    def should_remove_after_completion(self) -> bool:
        return True


def test_review_completion_does_not_repersist_state_or_recreate_removed_project(
    qapp,
    valid_settings_file: Path,
    monkeypatch,
) -> None:
    settings = SettingsStore(valid_settings_file).load()
    project = ProjectData(
        id=601,
        uid="uid-601",
        stage=AnnotationStage.REVIEW,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    repository = ProjectRepository(settings.data_dir)
    repository.create_local_project(project)
    paths = LabelingPaths(settings.data_dir, project.id)
    write_json(paths.cache_path, {"figures": {}, "review": {}})
    write_json(
        paths.runtime_state_path,
        {"item_id": 4, "duration_hours": 9.0, "processed_item_ids": [1, 2, 3]},
    )

    transfer = RecordingTransfer()
    api = AvailableApi()
    window = MainWindow(SettingsStore(valid_settings_file))
    window.current_project = project
    window.current_screen = CompletedScreen()
    window.completion_service = CompletionService(
        api_client=api,
        project_repository=repository,
        file_transfer=transfer,
        import_export_service=ImportExportService(settings.data_dir, transfer),
    )
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "information",
        lambda *args, **kwargs: None,
    )

    window.complete_project()

    assert api.completed == [("uid-601", 2.5)]
    assert transfer.uploaded == [("uid-601", "review.json")]
    assert window.current_project is None
    assert window.current_screen is None
    assert not ProjectPaths(settings.data_dir, project.id).project_dir.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_golden_parity_labeling_completion.py::test_review_completion_does_not_repersist_state_or_recreate_removed_project
```

Expected before fix: FAIL with `AssertionError: completion close must not call normal close_screen`.

- [ ] **Step 3: Add a completion close path**

In `annotation_tool/ui/main_window.py`, add:

```python
    def _discard_current_project_after_completion(self) -> None:
        # Completion already saved/exported/reset/removed the project. Calling the
        # normal screen close path here would persist stale runtime state and can
        # recreate a project directory that CompletionService just removed.
        if self.current_screen is not None:
            delete_later = getattr(self.current_screen, "deleteLater", None)
            if delete_later is not None:
                delete_later()

        self.current_project = None
        self.current_screen = None
        self.placeholder = QLabel("No project opened", self)
        self.placeholder.setStyleSheet("font-size: 18px;")
        self.setCentralWidget(self.placeholder)
        self.set_current_project_title(None)
```

In `complete_project`, replace:

```python
            self._close_current_project()
```

with:

```python
            self._discard_current_project_after_completion()
```

- [ ] **Step 4: Run the golden completion test**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_golden_parity_labeling_completion.py
```

Expected: PASS.

- [ ] **Step 5: Run existing completion tests**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_project_completion.py tests/test_annotation_export.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add annotation_tool/ui/main_window.py tests/test_golden_parity_labeling_completion.py
git commit -m "test: pin golden labeling completion parity"
```

---

### Task 3: Live Settings Propagation Golden Contract

**Files:**
- Create: `tests/test_golden_parity_overwrite_and_settings.py`
- Modify: `annotation_tool/ui/main_window.py`
- Modify: `annotation_tool/ui/screens/labeling_screen.py`
- Modify: `annotation_tool/services/labeling_session.py`

- [ ] **Step 1: Write failing test for settings applied to open screen**

Create `tests/test_golden_parity_overwrite_and_settings.py`:

```python
"""Golden overwrite and live-settings parity tests.

Tk baseline: origin/main 1dd11801066386f137f64ab2ad028005f325f463.
"""

from dataclasses import replace
from pathlib import Path

from PySide6.QtWidgets import QDialog, QMessageBox

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.models import ProjectData
from annotation_tool.core.paths import LabelingPaths
from annotation_tool.core.settings import SettingsStore
from annotation_tool.core.utils import read_json, write_json
from annotation_tool.infrastructure.repositories.labeling_repository import LabelingRepository
from annotation_tool.infrastructure.repositories.project_repository import ProjectRepository
from annotation_tool.services.import_export_service import ImportExportService
from annotation_tool.services.labeling_session import LabelingSession
from annotation_tool.services.project_service import ProjectService
from annotation_tool.ui import main_window as main_window_module
from annotation_tool.ui.main_window import MainWindow
from annotation_tool.ui.screens.labeling_screen import LabelingScreen
from tests.conftest import create_pattern_image
from tests.tk_era_fixture import create_tk_era_labeling_project_dir


def test_open_settings_applies_interface_style_to_real_labeling_session(
    qapp,
    valid_settings_file: Path,
    monkeypatch,
) -> None:
    store = SettingsStore(valid_settings_file)
    settings = store.load()
    create_tk_era_labeling_project_dir(
        settings.data_dir,
        project_id=702,
        uid="uid-702",
        item_id=0,
        labels=[{"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"}],
        images=[
            {
                "name": "a.jpg",
                "height": 10,
                "width": 20,
                "bboxes": [{"x1": 2, "y1": 2, "x2": 8, "y2": 7, "label": "car"}],
            }
        ],
        create_images=True,
    )
    project = ProjectData(
        id=702,
        uid="uid-702",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    window = MainWindow(store)
    window._set_project_screen(project)
    assert isinstance(window.current_screen, LabelingScreen)
    screen = window.current_screen
    assert screen.session.controller.annotation_style.bbox_line_width == 3.0

    new_settings = replace(
        settings,
        bbox_line_width=8.0,
        cursor_proximity_threshold=9.0,
        objects_opacity=0.5,
        color_fill_opacity=0.25,
        bbox_handler_size=7.0,
        keypoint_handler_size=6.0,
    )

    class AcceptedSettingsDialog:
        DialogCode = QDialog.DialogCode

        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return QDialog.DialogCode.Accepted

        def settings(self):
            return new_settings

    monkeypatch.setattr(main_window_module, "SettingsDialog", AcceptedSettingsDialog)

    window.open_settings()

    assert screen.session.annotation_style.bbox_line_width == 8.0
    assert screen.session.annotation_style.cursor_proximity_threshold == 9.0
    assert screen.session.controller.annotation_style.bbox_line_width == 8.0
    assert screen.session.controller.annotation_style.cursor_proximity_threshold == 9.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_golden_parity_overwrite_and_settings.py::test_open_settings_applies_interface_style_to_real_labeling_session
```

Expected before fix: FAIL because the real `LabelingSession` and current `FigureController` keep the old style.

- [ ] **Step 3: Implement style propagation**

In `annotation_tool/services/labeling_session.py`, add:

```python
    def apply_annotation_style(self, style: AnnotationStyle) -> None:
        self.annotation_style = style
        self.controller.annotation_style = style
```

In `annotation_tool/ui/screens/labeling_screen.py`, add:

```python
    def apply_annotation_style(self, style) -> None:
        self.session.apply_annotation_style(style)
        if self.session.item_count() > 0:
            self.refresh()
```

In `annotation_tool/ui/main_window.py`, after `_build_services()` in `open_settings`, add:

```python
        if self.current_screen is not None and hasattr(
            self.current_screen, "apply_annotation_style"
        ):
            self.current_screen.apply_annotation_style(
                AnnotationStyle.from_settings(self.settings)
            )
```

- [ ] **Step 4: Run settings tests**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_golden_parity_overwrite_and_settings.py tests/test_settings.py tests/test_interface_settings_application.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add annotation_tool/ui/main_window.py annotation_tool/ui/screens/labeling_screen.py annotation_tool/services/labeling_session.py tests/test_golden_parity_overwrite_and_settings.py
git commit -m "test: pin live settings parity"
```

---

### Task 4: Overwrite Golden Contract

**Files:**
- Modify: `tests/test_golden_parity_overwrite_and_settings.py`

- [ ] **Step 1: Add production-path overwrite test**

Append to `tests/test_golden_parity_overwrite_and_settings.py`. The module imports were added in Task 3; do not duplicate them here.

```python
class ReachableApi:
    def is_available(self) -> bool:
        return True


class DownloadingTransfer:
    def __init__(self, paths: LabelingPaths) -> None:
        self.paths = paths

    def download(self, uid: str, file_name: str, destination: Path, **kwargs) -> None:
        if file_name == self.paths.figures_path.name:
            write_json(
                destination,
                {
                    "a.jpg": {
                        "trash": False,
                        "bboxes": [
                            {"x1": 9, "y1": 1, "x2": 18, "y2": 8, "label": "truck"}
                        ],
                        "masks": {},
                        "kgroups": [],
                        "height": 10,
                        "width": 20,
                    }
                },
            )
            return
        if file_name == self.paths.review_path.name:
            write_json(destination, {})
            return
        if file_name == self.paths.meta_path.name:
            write_json(
                destination,
                {
                    "labels": [
                        {
                            "name": "truck",
                            "color": "blue",
                            "hotkey": "2",
                            "type": "BBOX",
                        }
                    ],
                    "review_labels": [],
                },
            )
            return
        raise AssertionError(f"unexpected download: {file_name}")


def test_overwrite_refreshes_real_labeling_session_without_stale_save(
    qapp,
    valid_settings_file: Path,
    monkeypatch,
) -> None:
    settings = SettingsStore(valid_settings_file).load()
    project = ProjectData(
        id=701,
        uid="uid-701",
        stage=AnnotationStage.ANNOTATE,
        mode=AnnotationMode.OBJECT_DETECTION,
    )
    paths = LabelingPaths(settings.data_dir, project.id)
    paths.ensure_project_dir()
    paths.images_dir.mkdir(parents=True, exist_ok=True)
    create_pattern_image(paths.images_dir / "a.jpg", size=(20, 10), base=(255, 255, 255))
    write_json(
        paths.cache_path,
        {
            "labels": [{"name": "car", "color": "red", "hotkey": "1", "type": "BBOX"}],
            "review_labels": [],
            "items": [{"name": "a.jpg", "width": 20, "height": 10, "requires_annotation": True}],
            "figures": {
                "a.jpg": {
                    "trash": False,
                    "bboxes": [{"x1": 2, "y1": 2, "x2": 8, "y2": 7, "label": "car"}],
                    "masks": {},
                    "kgroups": [],
                    "height": 10,
                    "width": 20,
                }
            },
            "review": {},
        },
    )

    window = MainWindow(SettingsStore(valid_settings_file))
    repository = LabelingRepository(settings.data_dir, project.id)
    session = LabelingSession(project, repository)
    screen = LabelingScreen(session)
    transfer = DownloadingTransfer(paths)
    window.current_project = project
    window.current_screen = screen
    window.api_client = ReachableApi()
    window.project_service = ProjectService(
        api_client=window.api_client,
        project_repository=ProjectRepository(settings.data_dir),
        import_export_service=ImportExportService(settings.data_dir, transfer),
    )

    class Progress:
        def update_progress(self, *args):
            pass

        def should_cancel(self):
            return False

        def mark_complete(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(window, "_progress", lambda title: Progress())
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "information",
        lambda *args, **kwargs: None,
    )

    window.overwrite_annotations()

    reloaded = session.controller.figures()
    assert len(reloaded) == 1
    assert (reloaded[0].x1, reloaded[0].y1, reloaded[0].x2, reloaded[0].y2) == (
        9,
        1,
        18,
        8,
    )
    assert reloaded[0].label == "truck"
    refreshed_label_names = {label.name for label in session.figure_labels}
    assert "truck" in refreshed_label_names
    assert "car" not in refreshed_label_names
    persisted = read_json(paths.cache_path)
    assert persisted["figures"]["a.jpg"]["bboxes"] == [
        {"x1": 9, "y1": 1, "x2": 18, "y2": 8, "label": "truck"}
    ]
```

- [ ] **Step 2: Run overwrite golden test**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q tests/test_golden_parity_overwrite_and_settings.py::test_overwrite_refreshes_real_labeling_session_without_stale_save
```

Expected: PASS if the existing overwrite reload fix remains intact. This is intentionally stronger than `tests/test_overwrite_flow.py::test_overwrite_runs_service_and_refreshes_current_item_on_accept`: it drives `MainWindow -> ProjectService -> ImportExportService -> LabelingScreen -> LabelingSession`, mutates `cache.json` via the overwrite service path, and proves the current controller and persisted cache both reflect the downloaded bbox instead of stale in-memory annotations.

- [ ] **Step 3: Commit**

```bash
git add tests/test_golden_parity_overwrite_and_settings.py
git commit -m "test: pin golden overwrite parity"
```

---

### Task 5: Golden Lane Command and Docs

**Files:**
- Modify: `docs/quality/pyside-release-readiness-2026-04-23.md`

- [ ] **Step 1: Run full golden lane**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q \
  tests/test_golden_parity_tk_migration.py \
  tests/test_golden_parity_labeling_completion.py \
  tests/test_golden_parity_overwrite_and_settings.py
```

Expected: all golden parity tests pass.

- [ ] **Step 2: Run full suite**

Run:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
```

Expected: all tests pass. Record exact pass count and runtime.

- [ ] **Step 3: Update readiness docs**

In `docs/quality/pyside-release-readiness-2026-04-23.md`, add a short subsection under “Test-backed release surface”:

```markdown
### Golden Tk parity lane

The suite now includes golden parity scenarios that drive PySide production paths against Tk-derived contracts:

- Tk-era local labeling project opens through `MainWindow._set_project_screen`
- labeling completion uploads the stage-specific artifact, resets runtime state, and does not recreate removed projects
- settings changes apply to an already-open labeling screen
- overwrite refresh reloads annotations without save-before-navigation clobbering
```

Update the verified result line to the exact full-suite output from Step 2.

- [ ] **Step 4: Commit docs**

```bash
git add docs/quality/pyside-release-readiness-2026-04-23.md
git commit -m "docs: record golden parity lane"
```

---

## Self-Review

- Spec coverage:
  - Fetch/verify Tk baseline: Baseline Rule.
  - Golden PySide production paths: Tasks 1-4.
  - End-to-end lifecycle boundary coverage: Task 2 completion, Task 3 settings, Task 4 overwrite, Task 1 migration/open.
  - Documentation and repeatable lane: Task 5.
- Placeholder scan:
  - No `TBD`, `TODO`, or “implement later” steps.
  - Each code-changing step includes concrete code.
- Type consistency:
  - `ProjectData`, `AnnotationStage`, `AnnotationMode`, `LabelingPaths`, `MainWindow`, `SettingsStore`, and `AnnotationStyle` names match existing code.
  - Test commands use the repository’s required offscreen lane.
