# Repository Guidelines

## Project Structure & Module Organization

This repository is the PySide6 candidate for the annotation tool. The main entry point is [annotation_tool/__main__.py](/home/yehor/Work/annotation_tool-pyside-audit/annotation_tool/__main__.py). The runtime code is organized by layer:

- `annotation_tool/ui/` for windows, dialogs, screens, widgets, and exception surfacing
- `annotation_tool/services/` for workflow and session orchestration
- `annotation_tool/infrastructure/` for API, unzip, file transfer, DB, and repository boundaries
- `annotation_tool/media/` for image and video helpers
- `annotation_tool/core/` for enums, models, settings, paths, utils, and exceptions
- `annotation_tool/annotation/` for figures, controllers, drawing, masks, and review-label logic
- `tests/` for the PySide pytest suite
- `templates/` for bundled HTML help assets
- `docs/quality/` for release-readiness and rehearsal notes carried in this repo

## Build, Test, and Development Commands

Use the local installers to create `venv/` and install dependencies:

```bash
bash install_linux.sh
source venv/bin/activate
python -m annotation_tool
```

Primary verification lane:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
```

Run that exact command when reporting test status unless a narrower test slice is explicitly more appropriate.

## Coding Style & Naming Conventions

Use Python with 4-space indentation, `snake_case` for functions and modules, and `PascalCase` for classes. Preserve the current layer split:

- UI logic stays in `ui/`
- workflow and application state coordination stays in `services/`
- file, API, and repository boundaries stay in `infrastructure/`
- persisted-path computation goes through `core/paths.py`

Do not bypass repository or service boundaries from screens unless the existing code already does so and the change is intentionally limited.

## Testing Guidelines

Prefer pytest coverage over manual claims. For UI-safe automated verification, use the offscreen Qt lane:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
```

If you only run a subset, state the exact test target. If a task affects release-readiness, update the relevant docs in `docs/quality/`.

## Release-Readiness Docs

The current handoff docs in this repo are:

- [docs/quality/pyside-release-readiness-2026-04-23.md](/home/yehor/Work/annotation_tool-pyside-audit/docs/quality/pyside-release-readiness-2026-04-23.md)
- [docs/quality/linux-release-rehearsal-runbook-2026-04-23.md](/home/yehor/Work/annotation_tool-pyside-audit/docs/quality/linux-release-rehearsal-runbook-2026-04-23.md)
- [docs/quality/production-safe-rehearsal-lane-2026-04-23.md](/home/yehor/Work/annotation_tool-pyside-audit/docs/quality/production-safe-rehearsal-lane-2026-04-23.md)

Use them as the current operational guide for:

- first-release scope status
- Linux promotion rehearsal
- production-safe local-only migration and rollback rehearsal

## Security & Configuration Tips

`settings.json` is local-only and should remain private. Keep real tokens and URLs there, not in source files. Local project data under `data/`, `venv/`, `.pytest_cache/`, and generated artifacts should remain uncommitted.

If the backend environment is production, do not run destructive or state-mutating rehearsal steps unless explicitly approved. Use the production-safe rehearsal lane doc when you need local-only migration proof.
