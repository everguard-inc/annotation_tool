# PySide Architecture Overview

This note documents the current PySide6 candidate architecture after reviewing the runtime code in `annotation_tool/`, the product requirements in `docs/product/`, and the release-readiness notes in `docs/quality/`.

The goal is to give maintainers a compact map of where behavior lives, how data moves, and which boundaries matter when changing annotation, filtering, or event-validation workflows.

## Layer Map

| Layer | Main paths | Responsibility |
| --- | --- | --- |
| Entry and shell | `annotation_tool/__main__.py`, `annotation_tool/ui/main_window.py`, `annotation_tool/ui/actions.py` | Start Qt, load settings, build services, route menu actions, mount the active project screen |
| UI screens | `annotation_tool/ui/screens/` | Translate canvas, keyboard, sidebar, and status-bar input into session calls |
| UI widgets | `annotation_tool/ui/widgets/` | Canvas coordinate mapping, status bars, class wheel, HTML windows |
| Services | `annotation_tool/services/` | Workflow state, navigation, timing/statistics, import/export, project completion |
| Repositories | `annotation_tool/infrastructure/repositories/` | Local persistence boundaries for project state and workflow caches |
| Infrastructure clients | `annotation_tool/infrastructure/` | Backend API, file transfer, unzip, SQLite compatibility setup |
| Annotation domain | `annotation_tool/annotation/` | Figure models, drawing, editing controller, masks, keypoint groups, review labels |
| Media | `annotation_tool/media/` | OpenCV frame/image helpers, barcode decoding, frame cache |
| Core | `annotation_tool/core/` | Enums, dataclasses, settings, paths, JSON utilities, exceptions |

## Runtime Composition

`MainWindow` is the composition root. After settings load, it builds:

- `ApiClient` for project listing and completion calls.
- `FileTransferClient` for artifact download/upload.
- `ProjectRepository` for local project directories and `state.json`.
- `ImportExportService` for mode-specific import/export files.
- `ProjectService` for open/download/overwrite orchestration.
- `CompletionService` for save, export, upload, backend completion, and local cleanup.

When a project opens, `MainWindow._set_project_screen()` chooses the workflow by `ProjectData.mode`:

| Mode | Paths | Repository | Session | Screen |
| --- | --- | --- | --- | --- |
| `OBJECT_DETECTION`, `SEGMENTATION`, `KEYPOINTS` | `LabelingPaths` | `LabelingRepository` | `LabelingSession` | `LabelingScreen` |
| `FILTERING` | `FilteringPaths` | `FilteringRepository` | `FilteringSession` | `FilteringScreen` |
| `EVENT_VALIDATION` | `EventValidationPaths` | `EventValidationRepository` | `EventValidationSession` | `EventValidationScreen` |

Each screen implements `BaseProjectScreen`, so the shell can call `save()`, `close_screen()`, `go_to_id()`, `reload_current_annotations()`, `export_results()`, and `should_remove_after_completion()` without knowing the workflow internals.

## Local Project Layout

All persisted paths should be computed through `annotation_tool/core/paths.py`.

```text
<data_dir>/data/<00000 project id>/
  state.json
  runtime_state.json
  statistics_<timestamp>.txt
  cache.json
  db.sqlite

  # Labeling
  meta.json
  figures.json
  review.json
  archive.zip
  images/

  # Filtering
  video.mp4
  selected_frames.json

  # Event validation
  archive.zip
  videos/
  images/
  event_validation_results.json
```

`db.sqlite` remains part of project validity and migration compatibility. Current workflow persistence is JSON-first:

- `state.json`: project id, uid, stage, and mode.
- `runtime_state.json`: current item, duration hours, processed item ids.
- `cache.json`: mode-specific working cache used by repositories.
- result files: exported artifacts uploaded during completion.

## Boundary Rules

- UI screens should not parse project files directly. They should call session methods.
- Sessions own workflow state, navigation, dirty current item behavior, timing, and status data.
- Repositories own the local cache schema and SQLite migration fallback.
- Import/export owns backend artifact shapes and local cache rebuilding.
- Annotation editing should stay in `annotation_tool/annotation/`; screens should not mutate figures directly.
- Persisted paths should come from `core/paths.py`; avoid hand-building `data/<project id>` paths.

## Shared Interaction Pattern

Most active workflows follow this shape:

```text
Qt input
  -> screen handler
  -> session method
  -> repository/cache update
  -> screen refresh
  -> canvas/status/sidebar update
```

Navigation follows a stricter pattern:

```text
go_to_item()
  -> track action and update duration
  -> save current item
  -> mark previous item as processed
  -> clamp and switch item id
  -> load new item
  -> persist runtime state
```

Filtering and labeling both use this pattern. Event validation follows the same pattern for event navigation and saves answers/comments through its repository.

## Import, Overwrite, Export, Completion

`ImportExportService` is the mode switch for backend artifacts:

- Labeling import downloads `meta.json`, `figures.json`, optional `review.json`, and `archive.zip`, validates image/annotation counts, injects a `blur` label when needed, then writes `cache.json`.
- Filtering import downloads `video.mp4` and `meta.json`, then seeds `cache.json` with labels and empty items.
- Event validation import downloads `archive.zip`, `meta.json`, optional `event_validation_results.json`, unzips media, validates result-field order, then writes `cache.json`.

Overwrite is intentionally narrower:

- Filtering overwrite is blocked with `UserVisibleError`.
- Labeling overwrite refreshes figures/review/meta and rebuilds the labeling cache.
- Event validation overwrite refreshes meta/results and rebuilds the event validation cache.

Completion saves the current screen, asks the screen for exported paths, uploads those files plus statistics when present, calls backend completion, updates local stage, resets runtime state, and optionally removes local files according to screen-specific cleanup rules.

## Testing Map

The primary verification lane is:

```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
```

Useful focused test areas:

| Area | Tests |
| --- | --- |
| Annotation editing and persistence | `tests/test_bbox_editing.py`, `tests/test_segmentation_masks.py`, `tests/test_keypoint_groups.py`, `tests/test_object_history_and_clipboard.py`, `tests/test_trash_and_review_labels.py` |
| Labeling import/export/overwrite | `tests/test_annotation_import.py`, `tests/test_annotation_export.py`, `tests/test_overwrite_flow.py`, `tests/test_overwrite_refresh_regression.py` |
| Filtering workflow | `tests/test_filtering_selection_navigation.py`, `tests/test_filtering_results_export.py`, `tests/test_filtering_video_provider.py`, `tests/test_filtering_barcode_decoder.py`, `tests/test_filtering_delay_preview.py` |
| Event validation | `tests/test_event_validation_repository.py`, `tests/test_event_validation_session.py`, `tests/test_event_validation_import_export.py`, `tests/test_event_validation_deferral.py` |
| Shared shell/runtime | `tests/test_main_window.py`, `tests/test_project_management.py`, `tests/test_project_completion.py`, `tests/test_session_state_persistence.py`, `tests/test_runtime_state_and_statistics.py` |

## Change Checklist

Before changing a workflow:

1. Identify the mode-specific path class, repository, session, and screen.
2. Confirm whether the change affects backend artifact shape, local `cache.json`, runtime state, or only rendering/input.
3. Keep screen changes thin; move workflow rules into the session or repository.
4. Add or update focused pytest coverage for the affected session/repository/screen.
5. Run the primary offscreen test lane or state the narrower command used.
