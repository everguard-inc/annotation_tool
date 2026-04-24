# Linux Release Rehearsal Log - 2026-04-23

## Operator

- Executor:
- Linux machine:
- Backend environment: production-derived Tk checkout used as read-only source
- Reference project ID: `21852` and `08071`
- Reference project mode: `FILTERING` and `OBJECT_DETECTION`
- Chosen lane: production-safe local-only rehearsal

## Preflight

- Tk commit: `1dd11801066386f137f64ab2ad028005f325f463`
- PySide commit: `5f58ac5822b599b7c975474351954a4b14c118c0`
- Tk git status: `## main...origin/main` with untracked `.codex`
- PySide git status: `## pyside-fr-audit...origin/pyside [ahead 15]` with untracked `.codex`, `AGENTS.md`, `CLAUDE.md`, and `docs/`
- PySide pytest command: `PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q`
- PySide pytest result observed on 2026-04-23: `92 passed in 0.77s`

## Inputs Checklist

- [x] One real non-EV project directory is available
- [x] Pristine backup path is recorded
- [x] Temporary `data_dir` is chosen
- [ ] GUI-capable Linux workstation is confirmed
- [ ] Backend credentials are available if the full rehearsal lane is chosen

## Source Projects

- Read-only Tk source repo: `/home/yehor/Work/annotation_tool`
- Absolute data dir discovered from the live machine: `/home/yehor/Data/labeling/data`
- Filtering project: `/home/yehor/Data/labeling/data/21852`
- Detection project: `/home/yehor/Data/labeling/data/08071`
- Important nuance: `08071` already contains `cache.json`, so it is not a pristine Tk-era labeling directory anymore
- Important nuance: `21852` is a real filtering project directory with `video.mp4`, but its SQLite content is currently empty:
  - `classification_image = 0`
  - `value = {item_id: 0, duration_hours: 0, processed_item_ids: []}`
- Important nuance: before the live re-download described below, the existing local copy of `21852/video.mp4` was stale and invalid:
  - `ffprobe` reported `moov atom not found`
  - OpenCV `VideoCapture(...).isOpened()` returned `False`

## Prepared Local-Only Rehearsal Environment

- Stable local-only `data_dir`: `/tmp/pyside-prod-safe-stable/data`
- Stable copied projects visible to PySide:
  - `8071 OBJECT_DETECTION ANNOTATE`
  - `21852 FILTERING FILTERING`
- Throwaway Tk repo copy: `/tmp/tk-rehearsal-repo`
- Throwaway PySide repo copy: `/tmp/pyside-rehearsal-repo`
- Both copied repos are configured to use:
  - `token = production-token-placeholder`
  - `api_url = http://127.0.0.1:9`
  - `file_url = http://127.0.0.1:9`
  - `data_dir = /tmp/pyside-prod-safe-stable/data`
- Validation completed:
  - copied Tk code resolves the offline `data_dir`
  - copied PySide code resolves the offline `data_dir`
  - copied PySide `ProjectRepository` lists both local projects

## Live Backend Download Into Canonical Data Dir

- Canonical Tk-configured data root on this machine is the absolute path `/home/yehor/Data/labeling`
- Note: the Tk `settings.json` literal is `home/yehor/Data/labeling` without the leading slash, so the PySide verification run used the explicit absolute path
- Used a temporary PySide settings file with the live credentials and service URLs copied from the local Tk settings.
- The actual token and service URLs are intentionally omitted from this committed log; they remain local-only in `settings.json`.
  - `data_dir = /home/yehor/Data/labeling`
- Drove the real PySide `MainWindow.download_project()` path for both target IDs:
  - `8071 OBJECT_DETECTION ANNOTATE`
  - `21852 FILTERING FILTERING`
- Backend note:
  - the API returned `8071` twice with the same UID `2f688b9a-8e3d-4560-9322-d876fe56dcca`
  - the live download run deduplicated by project ID before selecting targets

### Live download result - `08071`

- Project directory: `/home/yehor/Data/labeling/data/08071`
- `download_project()` completed without exception
- On-disk result after the run:
  - `meta.json`, `figures.json`, `review.json`, `images/`, `cache.json`, and `state.json` are present
  - `runtime_state.json` is still absent because the verification run suppressed screen creation during the download step
- Main DB observation:
  - `db.sqlite` hash changed from `96b51496ae4980491499f1b276fef04a498cb2c5e96c44f6b7c26fe9899054d2`
  - to `e204ff21c92a8aa78fca6ffab30c3a0271ae70f45b81fae819681a5901318d1b`
- Interpretation:
  - the real PySide download path refreshed the live labeling project successfully
  - because this was executed against the live data dir, DB hash drift here should be treated as a live-side-effect observation, not as the clean non-mutating migration proof used in the production-safe lane

### Live download result - `21852`

- Project directory: `/home/yehor/Data/labeling/data/21852`
- `download_project()` completed without exception
- On-disk result after the run:
  - `video.mp4`, `meta.json`, `cache.json`, `state.json`, and `db.sqlite` are present
  - `figures.json`, `review.json`, and `images/` are correctly absent for a filtering project
  - `runtime_state.json` is still absent immediately after the download step because the verification run suppressed screen creation
- Main DB observation:
  - `db.sqlite` hash changed from `a928d6f73a13ed50a77a86f625d57969cca4c120d0f1c9c9d3ebe0c4499d86cc`
  - to `9edd9ebf277dd0c6387245185dca488927da479c23c77f3d79450b9e2b4e32ff`
- Media observation:
  - after the live download, `ffprobe` recognizes `video.mp4` as a valid H.264 MP4
  - width `1920`, height `1080`, frames `5110`, duration `1703.334000`
- Interpretation:
  - the live PySide download replaced the stale invalid local `video.mp4` with a valid filtering video
  - this changes `21852` from an unusable stale local sample into a valid current filtering-open sample

### Live open verification after download - `21852`

- Ran an offscreen PySide open against the live downloaded project in `/home/yehor/Data/labeling`
- Result:
  - window title became `Project 21852`
  - `current_screen` was `FilteringScreen`
  - `items_count = 5110`
  - `runtime_state.json` exists after open
  - runtime state content: `item_id = 0`, `duration_hours = 0.0`, `processed_item_ids = []`
- Interpretation:
  - post-download filtering open now succeeds on the live data dir
  - `21852` is still weak migration evidence for preserved filtering selections because its SQLite `classification_image` rows remain `0`

## Corrected Headless Live End-To-End Verification

- A corrected temporary PySide settings file was written using the repo's nested `SettingsStore` shape, not a flattened JSON payload
- Canonical live data root used for this run: `/home/yehor/Data/labeling`
- Canonical live projects exercised:
  - `08071` `OBJECT_DETECTION` `ANNOTATE`
  - `21852` `FILTERING` `FILTERING`
- Backend visibility confirmed again:
  - API still returned `8071` twice with the same UID `2f688b9a-8e3d-4560-9322-d876fe56dcca`
  - API returned `21852` once with UID `101d2bce-bd46-469b-a3c7-24dea31e7438`
- Local visibility confirmed again:
  - both project directories existed in `/home/yehor/Data/labeling/data`

### End-to-end result - `08071`

- Real `download_project()` completed
- Open result:
  - screen class: `LabelingScreen`
  - items count: `1000`
  - figure labels count: `6`
  - review labels count: `8`
- Headless navigation result:
  - moved to item `1`
  - reopen also resumed at item `1`
- File-state result:
  - `db.sqlite` hash stayed `e204ff21c92a8aa78fca6ffab30c3a0271ae70f45b81fae819681a5901318d1b`
  - `cache.json` changed across download/open/close as expected
  - `runtime_state.json` changed across open/close as expected
  - `db.sqlite-wal` and `db.sqlite-shm` appeared after live SQLite usage
- Interpretation:
  - live detection reachability, download, open, persistence, and reopen are now directly verified offscreen

### End-to-end result - `21852`

- Real `download_project()` completed
- Open result:
  - screen class: `FilteringScreen`
  - items count: `5110`
  - barcode-derived current frame name resolved successfully
- Headless navigation result:
  - moved to item `1`
  - reopen also resumed at item `1`
- File-state result:
  - `db.sqlite` hash stayed `9edd9ebf277dd0c6387245185dca488927da479c23c77f3d79450b9e2b4e32ff`
  - `cache.json` changed across download/open/close as expected
  - `runtime_state.json` changed across open/close as expected
  - `db.sqlite-wal` and `db.sqlite-shm` appeared after live SQLite usage
- Interpretation:
  - live filtering reachability, download, open, frame decode, persistence, and reopen are now directly verified offscreen
  - this still does not prove preserved filtering selections because `classification_image` rows remain `0`

### Launch Commands

Tk copy:

```bash
cd /tmp/tk-rehearsal-repo
/home/yehor/Work/annotation_tool/venv/bin/python app.py
```

PySide copy:

```bash
cd /tmp/pyside-rehearsal-repo
PYTHONPATH=. /home/yehor/Work/annotation_tool-pyside-audit/venv/bin/python -m annotation_tool
```

## Isolated Display Findings

- `Xephyr` is available and was used to run an isolated display at `DISPLAY=:100`
- This avoided using the operator's live desktop mouse state for the rehearsal attempts

### Tk in `:100`

- Launch command succeeded inside the isolated display
- The startup background thread still emits a traceback from `remove_completed_projects()` when backend access fails fast
- Despite that, `Project > Open` followed the intended offline path:
  - Tk showed the expected backend-unreachable info dialog
  - after dismissing it, Tk showed `Select Project`
  - selecting the first entry changed the main window title to `Project 8071`
- Interpretation: Tk local-open fallback is functionally available in the production-safe lane, but the startup cleanup thread is not offline-safe

### PySide in `:100`

- Launch command succeeded inside the isolated display
- One GUI automation attempt raised an `Error` dialog
- Captured traceback on shutdown showed that the click path had triggered `download_project()`, not `open_project()`
- Separate code-level reproduction under a real `QApplication` with the same staged settings and data proved the intended path:
  - `project_service.get_available_projects()` returned local project `8071`
  - `MainWindow.open_project()` completed successfully for `8071`
  - `cache.json` was created
  - `runtime_state.json` was created
  - `db.sqlite` hash stayed unchanged
- Interpretation: PySide local-open fallback works on the staged data; the isolated-display GUI failure was an automation miss on the menu popup, not a product regression in `open_project()`

### Tk Reopen After PySide JSON Write

- Prepared a fresh staged copy of `08071`
- Let PySide perform first-open migration on that staged copy:
  - `cache.json` created
  - `runtime_state.json` created
  - `db.sqlite` hash remained `8bbdb202ac1dc8562d381bf07d417f66c77c42227cd9b817fd6b300c999defaf`
- Reopened the same copied project in Tk inside `:100`
- Result:
  - Tk again reached and opened `Project 8071`
  - `db.sqlite` hash remained unchanged
  - Tk created its usual `db.sqlite-wal` and `db.sqlite-shm` sidecars during its own SQLite usage
- Interpretation: on this real copied detection project, post-PySide-write rollback back into Tk is safe at least for the reopen path exercised here

## Automated Copy Checks

- Raw directory copies that include `db.sqlite-wal` and `db.sqlite-shm` are not stable evidence snapshots
- Reproduced behavior on copied `21852` and `08071`:
  - a plain SQLite read against the copied `db.sqlite` checkpoints WAL into the copied main DB
  - result: `db.sqlite` hash changes on the copy even before PySide-specific repository logic runs
- Conclusion: for automated local-only proof, use a read-only SQLite backup snapshot into `/tmp` before exercising PySide migrators

### Stable backup check - filtering `21852`

- Snapshot root: `/tmp/pyside-prod-safe-backed-up/data/21852`
- Result:
  - `cache.json` created: yes
  - `runtime_state.json` created: yes
  - `db.sqlite` hash unchanged before/after migrator read: yes
  - migrated items: `0`
  - migrated runtime state: `item_id = 0`, `duration_hours = 0.0`, `processed_item_ids = []`
- Interpretation: migration path is technically safe on the copied filtering project, but the project does not contain populated filtering rows, so this is only a minimal proof

### Fresh open-path check - filtering `21852`

- Fresh snapshot root: `/tmp/pyside-filtering-fresh/data/21852`
- Fresh staged-copy validation:
  - source `classification_image` rows: `0`
  - staged `classification_image` rows: `0`
  - source selected rows: `0`
  - staged selected rows: `0`
  - source `value` rows match staged `value` rows: yes
- Media validation:
  - `ffprobe` reports `moov atom not found` on the source `video.mp4`
  - OpenCV rejects the same source file with `isOpened() = False` and `frame_count = 0`
- PySide first-open result on the fresh staged copy:
  - `MainWindow.open_project()` reached filtering screen creation and then failed in `VideoFrameProvider.open()`
  - `db.sqlite` hash remained unchanged: `cfe599eddb8137ff5cbf03bb044511909172da4029f30518c8c735e850fe0743`
  - `runtime_state.json` was created from SQLite value migration
  - `cache.json` was not created because filtering cache bootstrap never reached the point where item names or selections could be read from frames
- Interpretation:
  - this stale pre-download snapshot did not add promotion evidence for filtering parity
  - the observed failure was tied to invalid local media, not to SQLite migration corruption
  - inference from the Tk source: Tk would reject the same staged project for the same reason because `annotation_widgets/image/filtering/logic.py` also gates filtering open on `cv2.VideoCapture(...).isOpened()`

### Stable backup check - detection `08071`

- Snapshot root: `/tmp/pyside-obj-backed-up/data/08071`
- Method note: removed only `cache.json` and `runtime_state.json` from the copied snapshot, never from the production source
- Result:
  - `cache.json` created: yes
  - `runtime_state.json` created: yes
  - `db.sqlite` hash unchanged before/after migrator read: yes
  - rebuilt cache item count: `1000`
  - rebuilt figures count: `1000`
  - rebuilt item and figure counts match the source `cache.json`: yes
  - migrated runtime state: `item_id = 0`, `duration_hours = 0.0`, `processed_item_ids = []`
- Interpretation: the labeling migrator can reconstruct a large real project from SQLite on a stable local-only copy without mutating the copied DB

## Drill Results

### Drill 1 - Upgrade Tk -> PySide

- Status: partial, automated local-only copy check completed
- Notes:
  - no headful Tk -> PySide GUI walkthrough yet
  - real copied-data migration evidence captured via stable SQLite backup snapshots in `/tmp`
  - strongest current proof is the labeling snapshot of `08071`
  - isolated-display Tk open of `8071` succeeded
  - isolated-display PySide `open_project()` was verified on the same staged data, but the GUI menu-driving attempt clicked the wrong action path
  - after the live re-download and corrected headless end-to-end pass, both `08071` and `21852` are verified live-open samples
  - filtering project `21852` still does not add preserved-selection migration evidence because its SQLite filtering rows are empty

### Drill 2 - Rollback After PySide Write

- Status: partial, reopen path verified on copied `08071`
- Notes:
  - PySide-generated `cache.json` and `runtime_state.json` did not block Tk reopen
  - Tk reopened the same copied project as `Project 8071`
  - live PySide open -> navigate -> close -> reopen also persisted correctly for both `08071` and `21852`
  - this is stronger than the earlier code-only proof, but still not a full human-reviewed visual parity pass after an in-app PySide edit action

### Drill 3 - Fresh Install

- Status: not run
- Notes:

### Drill 4 - In-App Update Tool

- Status: not run
- Notes:

## Stop Conditions Seen

- None yet

## Final Verdict

- Promotion recommendation: proceed on the promotion-minimum track
- Blocking issues:
  - human-reviewed Tk vs PySide visual comparison on `08071` and `21852` is not yet recorded
  - one explicit Tk rollback-after-PySide-write result on the live-downloaded working copy or a clearly documented equivalent is not yet recorded
  - backend-sensitive drills for fresh install, completion or upload, and in-app update-tool have not been run in a safe environment
  - the available real filtering project `21852` still does not prove preserved filtering-selection migration because it has zero `classification_image` rows
- Non-blocking follow-ups:
  - backend project list currently contains duplicate `8071` rows with the same UID
  - raw filesystem copies of live project dirs remain unstable evidence while `db.sqlite-wal` and `db.sqlite-shm` are present
  - Tk offline startup still throws a background-thread traceback from `remove_completed_projects()` when backend access fails fast
