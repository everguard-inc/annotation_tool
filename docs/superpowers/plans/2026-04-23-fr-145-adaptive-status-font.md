# FR-145 Adaptive Status-Bar Font Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the Tk resize-driven status-bar font-size clamp to `LabelingStatusBar` and `FilteringStatusBar`, closing the last uncited FR in the PySide first-release workbook.

**Architecture:** Each status-bar class gets a `resizeEvent(event)` override that computes `size = max(8, min(15, int(self.width() / 130)))` and applies it to every text label via `QFont(label.font())` → `setPointSize` → `label.setFont`. No shared base class; the two overrides are ~8 lines each and duplicating keeps each bar self-contained. Tests drive the resize under offscreen with `show() + processEvents()` before each `resize()` so the override actually fires.

**Tech Stack:** PySide6 (QWidget, QLabel, QFont), pytest, `QT_QPA_PLATFORM=offscreen`.

**Spec:** `docs/superpowers/specs/2026-04-23-fr-145-adaptive-status-font-design.md`.

---

## File Structure

**Modified:**
- `annotation_tool/ui/widgets/status_bar_labeling.py` — add `resizeEvent` override
- `annotation_tool/ui/widgets/status_bar_filtering.py` — add `resizeEvent` override
- `tests/test_status_bars.py` — add two FR-145 tests, update module docstring citation
- `docs/quality/pyside-test-disposition.md` — add FR-145 to test row, remove from gaps, bump coverage summary to 197/197
- `docs/quality/pyside-release-readiness-2026-04-23.md` — mark FR-145 covered

**Created:** none.

---

### Task 1: Add labeling status-bar resize override

**Files:**
- Modify: `annotation_tool/ui/widgets/status_bar_labeling.py`
- Test: `tests/test_status_bars.py`

- [ ] **Step 1: Write the failing test**

Append the following to `tests/test_status_bars.py`:

```python
def test_labeling_status_bar_scales_font_with_width(qapp) -> None:
    """Covers FR-145. Status-bar label point-size clamps to [8, 15] and
    tracks int(width / 130) between the bounds. Offscreen delivery
    requires show() + processEvents() before the resize dispatches."""
    bar = LabelingStatusBar()
    bar.show()
    qapp.processEvents()

    scaling_labels = (
        bar.mode_label,
        bar.class_label,
        bar.trash_label,
        bar.hidden_label,
        bar.item_id_label,
        bar.speed_label,
        bar.processed_label,
        bar.duration_label,
    )

    cases = [(300, 8), (1690, 13), (3000, 15)]
    for width, expected in cases:
        bar.resize(width, 30)
        qapp.processEvents()
        for label in scaling_labels:
            assert label.font().pointSize() == expected, (
                f"width={width} label={label.objectName() or label.text()} "
                f"got {label.font().pointSize()} expected {expected}"
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest tests/test_status_bars.py::test_labeling_status_bar_scales_font_with_width -v`

Expected: FAIL — label point-size does not track width (status bar has no `resizeEvent` override yet). Assertion mentions a point size that is the system default (not 8/13/15).

- [ ] **Step 3: Add the resize override**

In `annotation_tool/ui/widgets/status_bar_labeling.py`, change the import line and add a `resizeEvent` method at the end of the class. The full file becomes:

```python
from PySide6.QtGui import QFont, QResizeEvent
from PySide6.QtWidgets import QLabel, QProgressBar, QWidget, QHBoxLayout

from annotation_tool.core.models import LabelingStatusData


class LabelingStatusBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.mode_label = QLabel(self)
        self.class_label = QLabel(self)
        self.trash_label = QLabel(self)
        self.hidden_label = QLabel(self)
        self.item_id_label = QLabel(self)
        self.speed_label = QLabel(self)
        self.processed_label = QLabel(self)
        self.progress_bar = QProgressBar(self)
        self.duration_label = QLabel(self)

        self.progress_bar.setRange(0, 100)

        layout = QHBoxLayout(self)
        for widget in (
            self.mode_label,
            self.class_label,
            self.trash_label,
            self.hidden_label,
            self.item_id_label,
            self.speed_label,
            self.processed_label,
            self.progress_bar,
            self.duration_label,
        ):
            layout.addWidget(widget)

    def update_status(self, status: LabelingStatusData) -> None:
        percent = int((status.item_id + 1) / max(status.items_count, 1) * 100)

        self.mode_label.setText(f"Mode: {status.annotation_mode}: {status.annotation_stage}")
        self.class_label.setText(f"Class: {status.selected_class}")
        self.trash_label.setText("Trash" if status.is_trash else "not Trash")

        if status.figures_hidden:
            hidden_text = "All Hidden"
        elif status.review_labels_hidden:
            hidden_text = "Review Hidden"
        else:
            hidden_text = "All Visible"

        self.hidden_label.setText(hidden_text)
        self.item_id_label.setText(f"Img id: {status.item_id}")
        self.speed_label.setText(f"Speed: {status.speed_per_hour} img/hour")
        self.processed_label.setText(f"Position: {percent} % ({status.item_id + 1}/{status.items_count})")
        self.progress_bar.setValue(percent)
        self.duration_label.setText(f"Duration: {status.duration_hours:.2f} hours")

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        size = max(8, min(15, int(self.width() / 130)))
        for label in (
            self.mode_label,
            self.class_label,
            self.trash_label,
            self.hidden_label,
            self.item_id_label,
            self.speed_label,
            self.processed_label,
            self.duration_label,
        ):
            font = QFont(label.font())
            font.setPointSize(size)
            label.setFont(font)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest tests/test_status_bars.py::test_labeling_status_bar_scales_font_with_width -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add annotation_tool/ui/widgets/status_bar_labeling.py tests/test_status_bars.py
git commit -m "feat: scale labeling status-bar font to widget width (FR-145)"
```

---

### Task 2: Add filtering status-bar resize override

**Files:**
- Modify: `annotation_tool/ui/widgets/status_bar_filtering.py`
- Test: `tests/test_status_bars.py`

- [ ] **Step 1: Write the failing test**

Append the following to `tests/test_status_bars.py`:

```python
def test_filtering_status_bar_scales_font_with_width(qapp) -> None:
    """Covers FR-145 for filtering mode. Same clamp and divisor as the
    labeling bar; offscreen delivery requires show() + processEvents()
    before the resize dispatches."""
    bar = FilteringStatusBar()
    bar.show()
    qapp.processEvents()

    scaling_labels = (
        bar.mode_label,
        bar.delay_label,
        bar.selected_label,
        bar.item_id_label,
        bar.speed_label,
        bar.selected_ratio_label,
        bar.processed_label,
        bar.duration_label,
    )

    cases = [(300, 8), (1690, 13), (3000, 15)]
    for width, expected in cases:
        bar.resize(width, 30)
        qapp.processEvents()
        for label in scaling_labels:
            assert label.font().pointSize() == expected, (
                f"width={width} label={label.objectName() or label.text()} "
                f"got {label.font().pointSize()} expected {expected}"
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest tests/test_status_bars.py::test_filtering_status_bar_scales_font_with_width -v`

Expected: FAIL — filtering bar has no resize override yet; point-sizes stay at system default.

- [ ] **Step 3: Add the resize override**

In `annotation_tool/ui/widgets/status_bar_filtering.py`, change the import line and add a `resizeEvent` method at the end of the class. The full file becomes:

```python
from PySide6.QtGui import QFont, QResizeEvent
from PySide6.QtWidgets import QLabel, QProgressBar, QWidget, QHBoxLayout

from annotation_tool.core.models import FilteringStatusData


class FilteringStatusBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.mode_label = QLabel("Mode: Filtering", self)
        self.delay_label = QLabel(self)
        self.selected_label = QLabel(self)
        self.item_id_label = QLabel(self)
        self.speed_label = QLabel(self)
        self.selected_ratio_label = QLabel(self)
        self.processed_label = QLabel(self)
        self.progress_bar = QProgressBar(self)
        self.duration_label = QLabel(self)

        self.progress_bar.setRange(0, 100)

        layout = QHBoxLayout(self)
        for widget in (
            self.mode_label,
            self.delay_label,
            self.selected_label,
            self.item_id_label,
            self.speed_label,
            self.selected_ratio_label,
            self.processed_label,
            self.progress_bar,
            self.duration_label,
        ):
            layout.addWidget(widget)

    def update_status(self, status: FilteringStatusData) -> None:
        percent = int((status.item_id + 1) / max(status.items_count, 1) * 100)
        selected_ratio = status.selected_count / max(status.processed_count, 1) * 100

        self.delay_label.setText(f"Delay: {status.delay}")
        self.selected_label.setText("Selected: TRUE" if status.selected else "Selected: FALSE")
        self.item_id_label.setText(f"Img id: {status.item_id}")
        self.speed_label.setText(f"Speed: {status.speed_per_hour} img/hour")
        self.selected_ratio_label.setText(
            f"Selected: {selected_ratio:.2f}% ({status.selected_count} selected / {status.processed_count} viewed)"
        )
        self.processed_label.setText(f"Position: {percent} % ({status.item_id + 1}/{status.items_count})")
        self.progress_bar.setValue(percent)
        self.duration_label.setText(f"Duration: {status.duration_hours:.2f} hours")

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        size = max(8, min(15, int(self.width() / 130)))
        for label in (
            self.mode_label,
            self.delay_label,
            self.selected_label,
            self.item_id_label,
            self.speed_label,
            self.selected_ratio_label,
            self.processed_label,
            self.duration_label,
        ):
            font = QFont(label.font())
            font.setPointSize(size)
            label.setFont(font)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest tests/test_status_bars.py::test_filtering_status_bar_scales_font_with_width -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add annotation_tool/ui/widgets/status_bar_filtering.py tests/test_status_bars.py
git commit -m "feat: scale filtering status-bar font to widget width (FR-145)"
```

---

### Task 3: Update test module docstring citation

**Files:**
- Modify: `tests/test_status_bars.py`

- [ ] **Step 1: Update the module docstring**

Replace the current module docstring:

```python
"""Offscreen status-bar content-shape and update-regularly tests.

Covers FR-144, FR-146, FR-163.
"""
```

with:

```python
"""Offscreen status-bar content-shape, update-regularly, and adaptive-font tests.

Covers FR-144, FR-145, FR-146, FR-163.
"""
```

- [ ] **Step 2: Run the full status-bar test file to confirm no regression**

Run: `PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest tests/test_status_bars.py -v`

Expected: all tests pass (previous 5 + 2 new FR-145 tests).

- [ ] **Step 3: Commit**

```bash
git add tests/test_status_bars.py
git commit -m "docs: cite FR-145 in status-bars test module docstring"
```

---

### Task 4: Update pyside-test-disposition.md

**Files:**
- Modify: `docs/quality/pyside-test-disposition.md`

- [ ] **Step 1: Add FR-145 to the test_status_bars.py row**

Find the row starting with `| `tests/test_status_bars.py` |` (currently cites `FR-144, FR-146, FR-163`) and change the FR citations cell to:

```
FR-144, FR-145, FR-146, FR-163
```

Also update the "Notes" cell of that row to append `; FR-145 coverage landed 2026-04-23 via adaptive-font resize tests for both status bars`. The final row should read (single logical markdown row):

```
| `tests/test_status_bars.py` | UI shell | candidate-accept |  | `REQ-LABL-STATUS-001`, `REQ-FILT-STATUS-001` |  | FR-144, FR-145, FR-146, FR-163 | added 2026-04-23; offscreen status-bar content-shape + update-on-repeated-calls tests for both modes; FR-145 coverage landed 2026-04-23 via adaptive-font resize tests for both status bars |
```

- [ ] **Step 2: Remove FR-145 from the Coverage Gaps table**

Delete the FR-145 table row from the `## Coverage Gaps` section. After removal the table header remains but the body is empty — replace the table with this block so the section still reads cleanly:

```markdown
## Coverage Gaps

None. All 197 FR rows in the frozen workbook are now cited in PySide test docstrings as of 2026-04-23.
```

- [ ] **Step 3: Update the FR Coverage Summary bullets**

In the `## FR Coverage Summary` section, update the post-close bullets. The new final two lines should read:

```markdown
- 2026-04-23 coverage-close pass (roadmap step 3): 18 further FRs landed via new test files — `FR-001`, `FR-006`, `FR-009`, `FR-010`, `FR-020`, `FR-023`, `FR-025`, `FR-028`, `FR-066`, `FR-067`, `FR-068`, `FR-069`, `FR-144`, `FR-145`, `FR-146`, `FR-163`, `FR-174`, `FR-175`.
- Current cited FRs: 197 / 197 (100%).
- Remaining uncovered: 0.
```

(Replaces the prior bullets that claimed `17 further FRs landed`, `196 / 197`, and `Remaining uncovered: 1 FR (FR-145, explicitly deferred pending headful resize coverage)`.)

- [ ] **Step 4: Commit**

```bash
git add docs/quality/pyside-test-disposition.md
git commit -m "docs: mark FR-145 covered in pyside-test-disposition"
```

---

### Task 5: Update pyside-release-readiness-2026-04-23.md

**Files:**
- Modify: `docs/quality/pyside-release-readiness-2026-04-23.md`

- [ ] **Step 1: Update the Verdict section**

In the `## Verdict` list, remove the bullet:

```
- `FR-145` (status-bar font adapts to width) is deferred pending a headful resize harness.
```

The remaining bullets under Verdict are:

```markdown
- Event validation stays on Tk for the first PySide release.
- macOS stays on the Tk pin target and is out of scope for the first PySide release.
```

- [ ] **Step 2: Update "Functional coverage" bullets**

In the `### Functional coverage` subsection, replace the two bullets:

```
- The current disposition claims `196 / 197` FR coverage for the first-release target.
- The only explicit FR gap is `FR-145`, deferred for headful verification.
```

with:

```markdown
- The current disposition claims `197 / 197` FR coverage for the first-release target.
- There are no remaining FR gaps.
```

- [ ] **Step 3: Replace the FR-145 section**

In the `### FR-145` subsection under `## Explicit Non-Parity Areas`, replace the existing paragraph:

```
`FR-145` remains deferred because the current offscreen test lane cannot prove resize-driven font adaptation in status bars.
```

with:

```markdown
`FR-145` is now covered. `LabelingStatusBar` and `FilteringStatusBar` override `resizeEvent` to clamp each text label's point size to `max(8, min(15, int(width / 130)))`, matching the Tk reference formula. Coverage lives in `tests/test_status_bars.py::test_labeling_status_bar_scales_font_with_width` and `tests/test_status_bars.py::test_filtering_status_bar_scales_font_with_width`, both headless under `QT_QPA_PLATFORM=offscreen` using `show() + processEvents()` before the width changes.
```

- [ ] **Step 4: Commit**

```bash
git add docs/quality/pyside-release-readiness-2026-04-23.md
git commit -m "docs: mark FR-145 covered in pyside-release-readiness"
```

---

### Task 6: Run full suite and verify no regression

**Files:** none modified.

- [ ] **Step 1: Run the main verification lane**

Run: `PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q`

Expected: `101 passed` (99 before + 2 new FR-145 tests). All existing tests still green.

- [ ] **Step 2: Confirm git state is clean**

Run: `git status`

Expected: the six target files (two widget modules, `tests/test_status_bars.py`, two docs, no new untracked files related to this plan) are all committed. The branch sits 5 commits ahead of where this plan started.
