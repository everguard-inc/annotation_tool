# PySide Release Readiness - 2026-04-23

## Verdict

The PySide candidate is close to functionally ready for the approved first-release Linux scope, but it still requires the remaining promotion drills before being described as release-ready.

It is not full 1:1 parity with the Tk application, because macOS stays on the Tk pin target and is out of scope for the first PySide release.

## Verified Ground Truth

- PySide candidate repo: `/home/yehor/Work/annotation_tool-pyside-audit`
- PySide branch: `pyside-fr-audit`
- PySide commit at verification time: `pyside-fr-audit` after the 2026-04-24 PySide parity fixes
- Tk baseline code repo: `/home/yehor/Work/annotation_tool`
- PySide test command:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
```

- Verified result on 2026-04-24: `139 passed in 1.07s`

The current branch state is ahead of older roadmap or audit snapshots that still mention `84`, `90`, or `92` tests.

## Scope Interpretation

Two statements can both be true:

1. PySide has broad automated coverage for the approved "bare minimum" first-release scope defined by the frozen FR set, accepted ADRs, and the PySide test disposition.
2. PySide does not yet have literal full Tk parity across every mode, platform, and workflow.

The difference is mostly deliberate scope control, but release wording should remain conservative until the manual promotion gates are recorded.

## What Is Done

### Functional coverage

- The frozen workbook contains 197 FR rows.
- The current disposition claims `197 / 197` FR traceability for the first-release target.
- Recent audit fixes closed several previously hidden parity gaps in labeling export, keypoint label attributes, class-list keypoint details, and zoom math.
- Remaining readiness depends on the promotion gates below, not test count alone.

### Persistence compatibility

Tk-to-PySide migration is implemented through read-only migrators:

- `db.sqlite:value` -> `runtime_state.json`
- filtering `classification_image` -> `cache.json`
- labeling labels/images/bboxes/masks/keypoint_groups/review_labels -> `cache.json`
- event-validation events/fields -> `cache.json`

This means:

- first open of a Tk project in PySide seeds PySide JSON stores from SQLite
- SQLite remains intact
- pre-write rollback to Tk is safe by contract
- post-write rollback is intentionally lossy because Tk does not read PySide JSON stores

### Test-backed release surface

The PySide suite covers the first-release workflows broadly enough to treat the branch as real release work, not a prototype:

- project shell and menu wiring
- settings/bootstrap
- help/classes/review-label pages
- labeling bbox/mask/keypoint/history/class-switching flows
- filtering selection/navigation/export flows
- event-validation import/session/routing/export/completion flows
- overwrite flows
- Tk-to-PySide migration paths
- runtime persistence
- error dialogs and user-visible failure paths
- startup stale-project cleanup, cancellable transfer/unzip progress, and interface drawing settings

### Golden Tk parity lane

The suite now includes golden parity scenarios that drive PySide production paths against Tk-derived contracts:

- Tk-era local labeling project opens through `MainWindow._set_project_screen`
- labeling completion uploads the stage-specific artifact, resets runtime state, and does not recreate removed projects
- settings changes apply to an already-open labeling screen
- overwrite refresh reloads annotations without save-before-navigation clobbering

### Headless live-project evidence

The PySide candidate has also been exercised headlessly against the canonical live data root on this machine:

- `/home/yehor/Data/labeling/data/08071` opened as `LabelingScreen`
- `/home/yehor/Data/labeling/data/21852` opened as `FilteringScreen`
- both projects were visible through the PySide project flow
- both projects completed real `download_project()` runs without exception
- both projects survived open -> navigate -> close -> reopen cycles
- `db.sqlite` stayed unchanged during those open and reopen cycles
- PySide-owned JSON stores changed as expected:
  - `cache.json`
  - `runtime_state.json`

This does not replace the remaining manual promotion drills, but it reduces "can PySide actually reach, open, and persist these real projects?" as an open question.

## Explicit Scope Notes

### Event validation

Event validation is now in PySide first-release scope on Linux.

Automated coverage now includes:

- EV project download/import from `archive.zip`, `meta.json`, and prior `event_validation_results.json`
- EV answers/comment persistence in PySide `cache.json`
- Tk SQLite EV migration from `event` plus `value.fields`
- EV screen routing from the main project shell
- EV session navigation, answer updates, comments, and video-frame stepping
- EV export to `event_validation_results.json`
- EV completion upload through the existing completion service, with stage progression to `DONE`

Manual visual comparison for real EV project data is still recommended before promotion, but EV is no longer an intentional PySide deferral.

### FR-145

`FR-145` is now covered. `LabelingStatusBar` and `FilteringStatusBar` override `resizeEvent` to clamp each text label's point size to `max(8, min(15, int(width / 130)))`, matching the Tk reference formula. Coverage lives in `tests/test_status_bars.py::test_labeling_status_bar_scales_font_with_width` and `tests/test_status_bars.py::test_filtering_status_bar_scales_font_with_width`, both headless under `QT_QPA_PLATFORM=offscreen` using `show() + processEvents()` before the width changes.

### macOS

macOS is not part of the first PySide release. It remains pinned to a Tk lineage per the accepted release-path ADRs.

## Remaining Gate

The remaining blocker is operational, not architectural:

### Promotion-minimum track

The approved path is to promote on the narrowest evidence-backed track, not reopen feature scope.

What is already proven well enough for that track:

- offscreen pytest lane is green
- stable local-only migration proof exists for a real copied detection project
- Tk reopen after PySide JSON writes has been demonstrated on a copied detection project
- live backend download and live headless open/reopen have succeeded for both a detection project and a filtering project

What is still required before promotion:

1. One human-reviewed Tk vs PySide visual parity pass on the real projects now in use:
   - `08071` for detection
   - `21852` for filtering
2. One explicit Tk rollback check after a PySide write on the live-downloaded working copy or another clearly documented equivalent.
3. Backend-sensitive acceptance in a safe environment for:
   - fresh install -> configure -> download -> annotate -> reopen -> complete or upload
   - in-app `Project -> Update tool`

### Operational follow-ups that do not need to reopen scope

- the backend currently returns project `8071` twice with the same UID
- Tk still emits an offline startup traceback from `remove_completed_projects()` when backend access fails fast

Until those drills are recorded, PySide should be described as:

- close to functionally ready for the approved release scope
- not yet promoted as the Tk replacement

## Recommended Next Actions

1. Run the human-reviewed Tk vs PySide comparison on `08071` and `21852`.
2. Record one explicit Tk rollback-after-PySide-write result on the live-downloaded working copy or a clearly documented equivalent.
3. Execute the backend-sensitive fresh-install and update-tool drills in a safe environment.
4. If those pass, promote PySide for the approved Linux first-release scope without reopening deferred scope items.
