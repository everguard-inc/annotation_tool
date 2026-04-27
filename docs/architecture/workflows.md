# Workflow Design: Annotation, Filtering, Event Validation

This document focuses on the three active operator workflows in the PySide app. It is intentionally code-facing: each section names the files that currently implement the behavior.

## Common Workflow Contracts

### Screen Contract

Every mounted project screen inherits `BaseProjectScreen` and gives `MainWindow` a common control surface:

- `items_count` and `duration_hours` for dialogs and completion.
- `save()` before completion.
- `close_screen()` when the project/window closes.
- `go_to_id(item_id)` for Project > Go to ID.
- `reload_current_annotations()` after download-and-overwrite.
- `export_results()` for completion upload files.
- `should_remove_after_completion()` for local cleanup rules.

### State Contract

`SessionStateStore` persists runtime state to `runtime_state.json`:

- `item_id`
- `duration_hours`
- `processed_item_ids`

It can seed those values from old Tk-era SQLite `value` rows when JSON state does not exist.

### Timing Contract

Sessions call `StatisticsService.track_action(stage, message)` on navigation and meaningful input. The returned duration becomes the session's `duration_hours` and is reflected in status bars and completion.

## Annotation Workflow

### Files

- UI: `annotation_tool/ui/screens/labeling_screen.py`
- Session: `annotation_tool/services/labeling_session.py`
- Repository: `annotation_tool/infrastructure/repositories/labeling_repository.py`
- Figures/controller: `annotation_tool/annotation/`
- Paths: `LabelingPaths`

### Data Shape

`LabelingRepository` stores a normalized working cache:

```json
{
  "labels": [],
  "review_labels": [],
  "items": [
    {"name": "image.jpg", "width": 640, "height": 480, "requires_annotation": true}
  ],
  "figures": {
    "image.jpg": {
      "trash": false,
      "bboxes": [],
      "kgroups": [],
      "masks": {},
      "height": 480,
      "width": 640
    }
  },
  "review": {
    "image.jpg": []
  }
}
```

The repository can migrate the same logical data from old SQLite tables when `cache.json` is absent.

### Mode and Stage Behavior

`LabelingSession` derives `image_names` from the repository and project stage:

- `ANNOTATE` and most non-review stages: all sorted image names.
- `REVIEW`: only items where `requires_annotation` is true.
- `CORRECTION`: only images with review labels.

The active label catalog also depends on stage:

- `REVIEW`: use `review_labels`; clicks create `ReviewLabel` callouts.
- Other stages: use figure labels; clicks create or edit bboxes, masks, or keypoint groups.

### Input Flow

```text
ImageCanvas event
  -> LabelingScreen.handle_*()
  -> LabelingSession.set_cursor()
  -> LabelingSession.handle_*()
  -> FigureController.handle_*()
  -> LabelingScreen.refresh()
  -> LabelingSession.render_frame()
  -> ImageCanvas.set_image()
```

Keyboard shortcuts are handled by `LabelingScreen.handle_key_press()` and `handle_key_release()`:

- `w`/`p` next item, `q`/`o` previous item.
- `f` fit image.
- `shift` toggles controller shift mode.
- `space` finishes a segmentation polygon.
- `escape` cancels a segmentation polygon.
- `a` opens class wheel; releasing `a` selects the highlighted label.
- `d` delete selected, `g` delete all.
- `t` toggle trash outside review stage.
- `e`, `r`, `n`, `h`, `s` toggle render/display modes.
- `u` copies editable annotations from the previous image.
- `ctrl+z`, `ctrl+y`, `ctrl+c`, `ctrl+v` map to controller history/clipboard.
- Digits select labels by hotkey.

### Figure Editing

`FigureController` owns all mutable figure editing:

- `BBox`: drag creates a box; selected handles can move corners; tiny boxes are rejected.
- `Mask`: clicks build a polygon; normal mode fills the active label mask; shift mode removes from it; masks serialize as RLE.
- `KeypointGroup`: drag creates a bbox-like placement; label attributes provide keypoint layout and connections; individual points can move.
- `ReviewLabel`: one-click callout used during review.

History is controller-local. Loading a new image creates a fresh controller and seeds history with that image's figures.

### Persistence Flow

On navigation or close:

```text
LabelingSession.save_current_item()
  -> repository.load_image_annotations(image_name)
  -> serialize controller figures
  -> preserve trash in non-review stages
  -> write figures or review labels back to cache.json
```

Export during completion writes either:

- `figures.json` for annotate/correction style work.
- `review.json` for review stage.

### Important Edge Rules

- Trash is blocked in `REVIEW`.
- Editing is blocked when figures are hidden, except segmentation remains editable.
- The `blur` label is added during import if missing and is rendered by applying blur before drawing other visible figures.
- Overwrite refresh must call `reload_current_annotations()` so stale in-memory figures do not clobber newly downloaded annotations.

## Filtering Workflow

### Files

- UI: `annotation_tool/ui/screens/filtering_screen.py`
- Session: `annotation_tool/services/filtering_session.py`
- Repository: `annotation_tool/infrastructure/repositories/filtering_repository.py`
- Media: `annotation_tool/media/video_frame_provider.py`, `annotation_tool/media/barcode_decoder.py`
- Paths: `FilteringPaths`

### Data Shape

Filtering uses the same `cache.json` filename but a simpler shape:

```json
{
  "labels": [],
  "review_labels": [],
  "items": [
    {"item_id": 0, "name": "decoded-name.jpg", "selected": true}
  ]
}
```

`item_id` is the video frame index. `name` is decoded from a barcode when possible. Export uses names first and falls back to ids when names are absent.

### Input Flow

```text
FilteringScreen key handler
  -> FilteringSession method
  -> VideoFrameProvider / FilteringRepository
  -> FilteringScreen.refresh()
  -> current frame rendered with optional green selected border
```

Key behavior:

- `w`/`p` next frame, `q`/`o` previous frame.
- `d` or `k` toggles selected.
- `z` jumps to previous selected frame.
- `x` jumps to next selected frame.
- `s` toggles degraded preview.
- `1` through `4` select navigation delay: no delay, short, middle, long.
- `f` fits the current frame.

### Navigation and Selection

`FilteringSession.load_current_item()` requests the frame, decodes a name, and stores it through `FilteringRepository.save_item_name()`. When selection changes, the repository finds or creates the cache item by `item_id`, toggles `selected`, and flushes the cache.

When moving forward/backward, the session asks `VideoFrameProvider.prefetch()` in the movement direction. This keeps frame reads isolated from the UI screen.

### Export

`FilteringScreen.export_results()` writes `selected_frames.json`:

```json
{
  "names": ["decoded-name.jpg"],
  "ids": [15]
}
```

The screen flushes repository state first, then includes selected items only. Completion removes filtering projects locally after successful upload.

### Important Edge Rules

- Filtering overwrite is intentionally blocked by `ImportExportService.overwrite_annotations()`.
- Item names are opportunistic. Selection must still work when barcode decoding fails.
- The selected state is shown visually as a thick green frame border.

## Event Validation Workflow

### Files

- UI: `annotation_tool/ui/screens/event_validation_screen.py`
- Session: `annotation_tool/services/event_validation_session.py`
- Repository: `annotation_tool/infrastructure/repositories/event_validation_repository.py`
- Paths: `EventValidationPaths`

### Data Shape

Event validation cache stores question fields and event answers:

```json
{
  "fields": {
    "Is the event valid?": {
      "Yes": "green",
      "No": "red"
    }
  },
  "events": {
    "event-uid": {
      "answers": ["Yes"],
      "comment": ""
    }
  }
}
```

Import builds `fields` from `meta.json`, where each item has a question, answers, and colors. Existing `event_validation_results.json` is accepted only when its `fields` list matches the imported question order.

### Input and View Flow

```text
EventValidationScreen input/sidebar/playback
  -> EventValidationSession method
  -> EventValidationRepository save/load
  -> EventValidationScreen.refresh()
  -> canvas, sidebar, slider, playback controls, status bar
```

Key behavior:

- `w`/`p` next event, `q`/`o` previous event.
- `z` and `x` step video frames backward/forward.
- `a` switches to image mode when images exist.
- `s` switches to video mode.
- Digit keys cycle answers for the matching question index.
- Combo boxes update answers directly.
- Comment text updates the session comment.

Playback controls are screen-level Qt timers. The session only exposes frame navigation primitives and current-frame rendering.

### Media Loading

Each event uid maps to:

- `videos/<uid>.mp4`
- optionally `images/<uid>.jpg`

The session defaults to video mode and loads frames with OpenCV. It caps loaded frames at `MAX_EVENT_VALIDATION_VIDEO_FRAMES` to avoid unbounded memory use. If images are absent, `video_mode_only` prevents image mode.

### Persistence and Export

Answers are ordered by the current `fields` keys:

```text
EventValidationSession.save_current_item()
  -> repository.save_event(uid, list(answers.values()), comment)
  -> cache.json
```

Export writes `event_validation_results.json`:

```json
{
  "fields": ["Is the event valid?"],
  "events": {
    "event-uid": {
      "answers": ["Yes"],
      "comment": ""
    }
  }
}
```

Completion uploads this file and keeps the local event validation project by default.

### Important Edge Rules

- Empty or unreadable event videos raise `UserVisibleError`.
- Results-field mismatch between `meta.json` and imported results is a blocking error.
- `EventValidationRepository.count_incomplete()` exists as a repository-level readiness helper, but current `CompletionService.check_before_completion()` is still a generic pass-through.

## Design Notes for Future Changes

When adding workflow behavior, choose the layer by the type of change:

| Change type | Prefer this layer |
| --- | --- |
| Keyboard or widget wiring | screen |
| Navigation, current item state, timing, status values | session |
| Local cache schema or old SQLite migration | repository |
| Backend artifact download/upload/export shape | import/export service |
| Figure creation, hit testing, selection, serialization | annotation domain |
| Project open/download/overwrite/complete orchestration | project or completion service |

Avoid making screens aware of cache internals. If a screen needs data that is not already exposed, add a focused session method or status field.
