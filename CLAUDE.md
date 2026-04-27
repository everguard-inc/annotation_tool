# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Running and installing

- Linux install: `bash install_linux.sh`
- Run the app: activate `venv/` then `python -m annotation_tool`
- Main verification lane:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
```

Use that exact command when making repo-wide correctness claims unless a narrower lane is explicitly justified.

## What this project is

This is the PySide6 migration candidate for the annotation tool. It replaces the older Tk shell with a layered PySide architecture while preserving the approved first-release behavior set:

- object detection labeling
- segmentation labeling
- keypoint labeling
- filtering workflows
- event validation workflows
- help and settings flows
- local project reopen and runtime persistence

macOS remains outside the PySide first-release scope and stays on the Tk pin target.

## Architecture

The repo is split into stable layers:

- `annotation_tool/ui/`
  - `main_window.py`
  - dialogs
  - screens
  - widgets
- `annotation_tool/services/`
  - project open or download orchestration
  - completion
  - import or export
  - runtime session state
  - labeling and filtering sessions
- `annotation_tool/infrastructure/`
  - API client
  - file transfer
  - unzip
  - DB wrapper
  - repositories
- `annotation_tool/media/`
  - frame providers
  - converters
  - barcode decode helpers
- `annotation_tool/core/`
  - enums
  - models
  - settings
  - paths
  - exceptions
  - utils
- `annotation_tool/annotation/`
  - figures
  - controllers
  - drawing
  - segmentation and keypoint helpers

Preserve these boundaries when editing:

- screens should talk to sessions or services, not directly to backend APIs
- repositories own persisted JSON and migration reads
- settings and path conventions belong in `core/`
- import/export and completion behavior should stay centralized in services

## Persistence model

PySide uses JSON stores as the active source of truth:

- `runtime_state.json`
- `cache.json`

Compatibility with Tk is handled through read-only migrators that seed those files from legacy `db.sqlite` on first open. Do not casually introduce SQLite writes back into the PySide flow unless that policy is being changed deliberately and documented.

## Release-readiness guidance

The current operational docs in this repo are:

- [docs/quality/pyside-release-readiness-2026-04-23.md](/home/yehor/Work/annotation_tool-pyside-audit/docs/quality/pyside-release-readiness-2026-04-23.md)
- [docs/quality/linux-release-rehearsal-runbook-2026-04-23.md](/home/yehor/Work/annotation_tool-pyside-audit/docs/quality/linux-release-rehearsal-runbook-2026-04-23.md)
- [docs/quality/production-safe-rehearsal-lane-2026-04-23.md](/home/yehor/Work/annotation_tool-pyside-audit/docs/quality/production-safe-rehearsal-lane-2026-04-23.md)

The key status to remember:

- PySide is close to functionally ready for the approved first-release Linux scope, pending the remaining promotion drills
- event validation is in the Linux PySide scope
- `FR-145` adaptive status-bar font behavior is covered
- Linux promotion drills and human parity review remain the promotion gate

## Production safety

Be careful with backend-mutating paths:

- completion uploads artifacts and calls task completion
- download and overwrite paths can mutate local project state based on remote state
- ordinary project open tries the backend first before falling back to local projects

If the working backend is production and the task is only to prove migration or rollback safety, prefer the production-safe rehearsal lane and force local-only behavior rather than touching live task state.

## Testing and doc updates

When behavior changes:

- update or add pytest coverage in `tests/`
- run the relevant test command
- update the release docs if the change affects readiness, rehearsal, or scope claims

When docs disagree with fresh verification, prefer fresh verification and then fix the docs explicitly.
