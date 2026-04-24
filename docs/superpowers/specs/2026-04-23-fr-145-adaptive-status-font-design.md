# FR-145 Adaptive Status-Bar Font — Design

Closes the last uncited FR in the PySide first-release workbook.

## Requirement

FR-145 (workbook-crosswalk row): the status bar must adapt its font size to the
window width. The Tk reference (`annotation_widgets/image/labeling/gui.py:73-81`
and `annotation_widgets/image/filtering/gui.py:70-81`) does this with:

```python
new_font_size = max(8, min(15, int(self.winfo_width() / 130)))
label_font = font.Font(family="Ubuntu Condensed", size=new_font_size)
for widget in [...text labels...]:
    widget.config(font=label_font)
```

PySide ports the size formula and scope but not the hardcoded font family.

## Behavior

When `LabelingStatusBar` or `FilteringStatusBar` is resized, every text label in
the bar updates its font point-size to:

```
size = max(8, min(15, int(width / 130)))
```

where `width` is the status-bar widget's width at the time of the resize event.
The `QProgressBar` is not touched. The font family of each label is preserved —
only the point size changes. The floor (8) and ceiling (15) match the Tk
reference clamp exactly.

## Implementation

Add a `resizeEvent(event)` override to both classes in
`annotation_tool/ui/widgets/status_bar_labeling.py` and
`annotation_tool/ui/widgets/status_bar_filtering.py`. Each override:

1. calls `super().resizeEvent(event)`
2. computes `size = max(8, min(15, int(self.width() / 130)))`
3. iterates over the bar's text labels (the same tuple already used for
   layout, minus the `QProgressBar`), clones each label's current `QFont` via
   `QFont(label.font())`, calls `setPointSize(size)` on the copy, and
   re-applies with `label.setFont(...)`

No shared base class or mixin. The two overrides are ~8 lines each and
duplicating them keeps each bar self-contained; DRYing them up would cost
more indirection than it saves for two consumers.

## Tests

Extend `tests/test_status_bars.py` (which already cites FR-144/146/163) with
one new test per bar. Each test:

- instantiates the bar,
- calls `bar.show()` and `qapp.processEvents()` to realize the widget so
  that subsequent `resizeEvent` dispatches reach the override (unshown
  `QWidget.resize()` only updates geometry and does not deliver
  `resizeEvent` — verified empirically under the offscreen platform),
- calls `bar.resize(width, 30)` at a narrow, mid, and wide width, each
  followed by `qapp.processEvents()` to flush the resize event,
- asserts the `.font().pointSize()` of every label in the bar's scaling
  set matches the expected clamped value (not just one label — verifies
  the whole iteration scope).

Width targets and expected sizes (same formula for both bars):

| width | `int(width / 130)` | clamped |
|-------|--------------------|---------|
| 300   | 2                  | 8       |
| 1690  | 13                 | 13      |
| 3000  | 23                 | 15      |

Docstrings cite FR-145.

Verification runs under `PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q`
per CLAUDE.md. The prior disposition's "headful harness required" rationale
rested on an incomplete reading of Qt event delivery: under the offscreen
platform plugin, `QWidget.show()` followed by `qapp.processEvents()` does
realize the widget and dispatches `resizeEvent` on subsequent `resize()`
calls. That pattern is already used by the existing
`test_canvas_refits_image_when_viewport_shrinks` regression, so the cost of
the new coverage is the `show()` prelude, not a new test harness.

## Doc updates

- `docs/quality/pyside-test-disposition.md`:
  - add FR-145 to the `tests/test_status_bars.py` row's FR-citations column
  - remove the FR-145 row from the "Coverage Gaps" table
  - update the "FR Coverage Summary" bullets: current cited FRs 196/197 → 197/197,
    "Remaining uncovered: 1" → "Remaining uncovered: 0", note the 2026-04-23
    close pass now includes FR-145
- `docs/quality/pyside-release-readiness-2026-04-23.md`:
  - update the "Verdict" bullet that calls FR-145 deferred
  - update the `### FR-145` section to note it is now covered, with a link to
    the new tests

## Out of scope

- Porting the Tk `"Ubuntu Condensed"` font family — see the brainstorming
  decision (option B). Cross-distro portability concern; the FR wording only
  names "font size".
- Scaling the progress-bar chunk text.
- Changing the divisor or clamp bounds away from the Tk values.
- Any other status-bar layout or content changes.
