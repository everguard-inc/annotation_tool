# Linux Release Rehearsal Runbook - 2026-04-23

This runbook turns the release-rehearsal checklist into an operator procedure tied to the actual local repos and revisions currently in use.

## Scope

Use this when you are ready to validate that the PySide candidate can replace the Tk build for supported Linux users.

This runbook does not change code. It is an execution guide for the manual release drills that still gate promotion.

## Repos And Revisions

- PySide candidate repo: `/home/yehor/Work/annotation_tool-pyside-audit`
- PySide branch: `pyside-fr-audit`
- PySide commit at time of writing: `pyside-fr-audit` after the 2026-04-24 PySide parity fixes
- Tk baseline code repo: `/home/yehor/Work/annotation_tool`
- Tk baseline commit: `1dd11801066386f137f64ab2ad028005f325f463`

## Verified Automated Baseline

The PySide candidate currently verifies with:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
```

Expected current result:

```text
139 passed
```

## Required Inputs Before You Start

Do not begin drill 1 until all of these exist:

- A real Linux workstation where you can launch the GUI.
- A pristine backup of one real Tk-era project directory outside the app `data_dir`.
- Real backend credentials that are valid for the same backend environment as that project.
- Enough disk space for:
  - pristine backup
  - Tk working copy
  - PySide working copy
  - rollback snapshot

## Required Operator Decisions

Record these before starting:

- rehearsal executor name
- Linux machine details
- reference project mode:
  - preferred: `OBJECT_DETECTION`
  - also acceptable: `SEGMENTATION`, `KEYPOINTS`, `FILTERING`
  - not acceptable for this rehearsal: `EVENT_VALIDATION`
- reference project ID
- backend environment:
  - production
  - staging
  - other explicit environment name

## Required Files And Paths

You need to know or choose these concrete paths up front:

- pristine project backup:
  - example: `/tmp/pyside-rehearsal/pristine/00042`
- working `data_dir` for Tk and PySide:
  - example: `/tmp/pyside-rehearsal/data`
- rollback snapshot copy after PySide write:
  - example: `/tmp/pyside-rehearsal/post-pyside-write/00042`

The project must contain:

- `state.json`
- `db.sqlite`
- `meta.json`
- and at least one mode-specific output file:
  - `figures.json`
  - `review.json`
  - or `selected_frames.json`

## Logging Target

Record the run in a local log or a copy of the checklist. This repo currently carries the runbook, not the authoritative historical rehearsal log from the docs repo.

## Preflight Commands

Run and record these first:

```bash
git -C /home/yehor/Work/annotation_tool rev-parse HEAD
git -C /home/yehor/Work/annotation_tool-pyside-audit rev-parse HEAD
git -C /home/yehor/Work/annotation_tool status --short
git -C /home/yehor/Work/annotation_tool-pyside-audit status --short
```

Expected:

- Tk repo points at `1dd11801066386f137f64ab2ad028005f325f463`
- PySide repo points at the rehearsal-approved commit
- no unexpected local code changes in the PySide repo

## Drill 1 - Upgrade Tk -> PySide On A Real Project Dir

### Purpose

Prove the read-only migrator path on real data.

### Setup

Create a fresh rehearsal area:

```bash
mkdir -p /tmp/pyside-rehearsal/pristine
mkdir -p /tmp/pyside-rehearsal/data/data
```

Copy the pristine project backup into the working `data_dir`:

```bash
cp -r <PRISTINE_PROJECT_DIR> /tmp/pyside-rehearsal/data/data/<ZERO_PADDED_PROJECT_ID>
```

### Tk pass

Prepare Tk:

```bash
cd /home/yehor/Work/annotation_tool
git checkout 1dd11801066386f137f64ab2ad028005f325f463
bash install_linux.sh
```

Point Tk `settings.json` to:

- your real backend credentials
- `data_dir = /tmp/pyside-rehearsal`

Launch Tk:

```bash
cd /home/yehor/Work/annotation_tool
source venv/bin/activate
python3 app.py
```

In Tk:

1. Open the reference project.
2. Confirm it loads normally.
3. Record:
   - current item
   - duration
   - one visible label
   - one visible figure or selected frame state
4. Close Tk cleanly.

Before switching to PySide, capture SQLite mtime:

```bash
stat /tmp/pyside-rehearsal/data/<ZERO_PADDED_PROJECT_ID>/db.sqlite
```

### PySide pass

Prepare PySide:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
git checkout pyside-fr-audit
bash install_linux.sh
```

Launch PySide against the same effective settings:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
source venv/bin/activate
python -m annotation_tool
```

In PySide:

1. Open the same project.
2. Verify:
   - project opens without error dialog
   - current item matches Tk close position
   - duration is continuous
   - label catalog is populated
   - at least one migrated figure is visible
3. Confirm new files exist:
   - `cache.json`
   - `runtime_state.json`
4. Confirm `db.sqlite` still exists and its mtime did not change.
5. Add one new annotation or selection.
6. Move forward one item.
7. Close PySide cleanly.

File checks:

```bash
ls -l /tmp/pyside-rehearsal/data/<ZERO_PADDED_PROJECT_ID>
stat /tmp/pyside-rehearsal/data/<ZERO_PADDED_PROJECT_ID>/db.sqlite
```

Pass criteria:

- all migration-visible state survives
- PySide JSON stores appear
- SQLite is unchanged
- no migration error dialogs

## Drill 2 - Rollback After A PySide Write

### Purpose

Validate the documented mixed-version policy after a PySide write.

### Snapshot

Copy the post-write project dir before reopening in Tk:

```bash
mkdir -p /tmp/pyside-rehearsal/post-pyside-write
cp -r /tmp/pyside-rehearsal/data/<ZERO_PADDED_PROJECT_ID> /tmp/pyside-rehearsal/post-pyside-write/
```

### Tk rollback pass

```bash
cd /home/yehor/Work/annotation_tool
git checkout 1dd11801066386f137f64ab2ad028005f325f463
bash install_linux.sh
source venv/bin/activate
python3 app.py
```

In Tk:

1. Open the same project.
2. Observe which documented outcome occurs:
   - supported rollback to pre-PySide visible state
   - or explicit documented block
3. Confirm Tk does not crash.

Schema sanity check:

```bash
sqlite3 /tmp/pyside-rehearsal/data/<ZERO_PADDED_PROJECT_ID>/db.sqlite '.schema'
```

Pass criteria:

- SQLite remains readable
- Tk either opens safely or blocks clearly
- no silent corruption of Tk-side persisted state

## Drill 3 - Fresh Install From Clean State

### Purpose

Validate a first-time Linux user flow on PySide.

### Clean area

Use a clean checkout or a fresh clone of the PySide repo. At minimum, ensure:

```bash
rm -rf /tmp/pyside-fresh-install-data
mkdir -p /tmp/pyside-fresh-install-data
```

Then:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
git checkout pyside-fr-audit
bash install_linux.sh
```

Launch:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
source venv/bin/activate
python -m annotation_tool
```

In the app:

1. Confirm settings dialog appears on first launch if required settings are missing.
2. Fill:
   - token
   - api_url
   - file_url
   - data_dir = `/tmp/pyside-fresh-install-data`
3. Download a small non-EV project.
4. Open it.
5. Add one annotation or filtering selection.
6. Navigate once.
7. Close the app.
8. Reopen and confirm runtime state persisted.
9. Complete the project and confirm server acceptance.

Pass criteria:

- install succeeds
- first-launch settings flow works
- download/open/edit/reopen/complete path succeeds end to end

## Drill 4 - In-App Update Tool

### Purpose

Validate Linux hard-cutover behavior from an older PySide revision.

### Preparation

Choose a prior revision on `pyside-fr-audit` or another approved PySide commit that still contains the update action.

Record before state:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
git rev-parse HEAD
git status --short
```

Install and launch:

```bash
bash install_linux.sh
source venv/bin/activate
python -m annotation_tool
```

In the app:

1. Open any non-EV local project so project actions are enabled.
2. Trigger `Project -> Update tool`.
3. Capture the dialog text.
4. Close and relaunch.

Record after state:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
git rev-parse HEAD
git status --short
```

Pass criteria:

- `HEAD` advances or reports already up to date
- dialog shows raw git output and reopen guidance
- app still launches after update
- working tree is clean after update

## Immediate Stop Conditions

Stop the rehearsal and record a blocker if any of these occur:

- Tk-era project opens in PySide with empty labels or empty figures
- `duration_hours` or current item resets unexpectedly
- `db.sqlite` mtime changes during the migrator drill
- Tk crashes reopening the project after a PySide write
- update tool leaves the repo dirty
- fresh install cannot reach usable first-launch settings flow

## What You Need Before Drill 1

The only missing operator inputs are:

- one real non-EV project directory
- the exact path to its pristine backup
- real backend credentials
- a chosen temporary `data_dir`
- confirmation that you are running on the Linux box intended for promotion evidence

## Recommended Execution Order

1. Decide the reference project and backend environment.
2. Copy the checklist into a working note.
3. Run drill 1 and drill 2 on the same project.
4. Run drill 3 on a fresh data dir.
5. Run drill 4 last, because it mutates the checked-out PySide revision.
