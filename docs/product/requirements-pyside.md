# PySide Requirements

## Baseline

- Canonical baseline commit: `1dd11801066386f137f64ab2ad028005f325f463`
- Source inputs during Phase 1: pinned `main` behavior inventory, frozen workbook crosswalk, approved ADRs, and the prepared `origin/pyside` `tests/` suite
- Default tag for this first pass: `baseline-from-main` unless a later ADR approves a delta, defer, or unknown classification
- Input precedence note: the prepared `origin/pyside` tests are candidate coverage input that helps surface workflow and FR coverage, but they do not override the pinned Tk baseline or become release truth until traced to requirement IDs and accepted through the documented test-disposition process
- Branch-placement note: when those prepared `origin/pyside` tests act as target-state specs for the PySide line, their citation updates may land on a PySide development branch before they land anywhere else; they do not need to be backported into the deployed Tk `main` tree just to remain valid migration input

## Release-Scoped Workflow Freeze

| Workflow ID | Priority tier | First-pass requirement ID |
| --- | --- | --- |
| WF-PROJ-BOOTSTRAP | P1 | REQ-PROJ-BOOTSTRAP-001 |
| WF-PROJ-OPEN | P1 | REQ-PROJ-OPEN-001 |
| WF-PROJ-DOWNLOAD | P1 | REQ-PROJ-DOWNLOAD-001 |
| WF-PROJ-REMOVE | P2 | REQ-PROJ-REMOVE-001 |
| WF-PROJ-GOTO | P2 | REQ-PROJ-GOTO-001 |
| WF-PROJ-RUNTIME | P1 | REQ-PROJ-RUNTIME-001 |
| WF-PROJ-COMPLETE | P1 | REQ-PROJ-COMPLETE-001 |
| WF-PROJ-UPDATE | P2 | REQ-PROJ-UPDATE-001 |
| WF-HELP-HOW | P2 | REQ-HELP-HOW-001 |
| WF-HELP-HOTKEYS | P2 | REQ-HELP-HOTKEYS-001 |
| WF-PROJ-SETTINGS | P2 | REQ-PROJ-SETTINGS-001 |
| WF-CANV-VIEWPORT | P1 | REQ-CANV-VIEWPORT-001 |
| WF-CANV-INPUT | P1 | REQ-CANV-INPUT-001 |
| WF-CANV-RENDER | P2 | REQ-CANV-RENDER-001 |
| WF-FILT-SELECT | P1 | REQ-FILT-SELECT-001 |
| WF-FILT-JUMP | P2 | REQ-FILT-JUMP-001 |
| WF-FILT-DELAY | P2 | REQ-FILT-DELAY-001 |
| WF-FILT-DATA | P1 | REQ-FILT-DATA-001 |
| WF-LABL-SWITCH | P1 | REQ-LABL-SWITCH-001 |
| WF-LABL-OVERWRITE | P2 | REQ-LABL-OVERWRITE-001 |
| WF-LABL-HELP | P2 | REQ-LABL-HELP-001 |
| WF-LABL-CLASS | P2 | REQ-LABL-CLASS-001 |
| WF-LABL-HISTORY | P2 | REQ-LABL-HISTORY-001 |
| WF-LABL-TRASH | P2 | REQ-LABL-TRASH-001 |
| WF-LABL-BBOX | P1 | REQ-LABL-BBOX-001 |
| WF-LABL-MASK | P1 | REQ-LABL-MASK-001 |
| WF-LABL-KPOINT | P1 | REQ-LABL-KPOINT-001 |
| WF-EVAL-ANSWER | P1 | REQ-EVAL-ANSWER-001 |
| WF-EVAL-VIEW | P1 | REQ-EVAL-VIEW-001 |
| WF-EVAL-OVERWRITE | P2 | REQ-EVAL-OVERWRITE-001 |

## Requirement Records

### REQ-PROJ-BOOTSTRAP-001

- Workflow ID: `WF-PROJ-BOOTSTRAP`
- Tag: `baseline-from-main`
- User outcome: App starts only after required settings exist and the data directory is usable
- Preconditions: The desktop app is launched and the settings store may contain missing required values.
- Trigger: Launch `app.py`
- Expected visible result: Settings dialog opens if required values are empty; main window opens after settings are valid
- Expected persisted result: `settings.json` is saved with mode/interface values; `data_dir` is created when possible
- Expected backend side effect: none
- Failure behavior: invalid `data_dir` resets the stored value and raises a message-box exception
- Evidence refs: `app.py:Application.__init__`; `config.py:Settings`; `gui_utils.SettingsManager`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-BOOTSTRAP-001`

### REQ-PROJ-OPEN-001

- Workflow ID: `WF-PROJ-OPEN`
- Tag: `baseline-from-main`
- User outcome: User opens an assigned or already-downloaded project into the main widget shell
- Preconditions: The main window is running and project actions are available from the Project menu.
- Trigger: `Project > Open` then select a project
- Expected visible result: Loading window appears, a selector opens, the previous widget is closed if needed, and the window title changes to `Project <id>`
- Expected persisted result: local project initialization may refresh DB/state before saving `state.json` for the chosen project
- Expected backend side effect: requests project list from the API when reachable
- Failure behavior: on API failure, falls back to local projects only and shows an info dialog
- Evidence refs: `main.py:MainWindow.open_project`; `annotation_widgets/factory.py:get_widget`; `annotation_widgets/io.py:initialize_project`; `path_manager.py:get_local_projects_data`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-OPEN-001`

### REQ-PROJ-DOWNLOAD-001

- Workflow ID: `WF-PROJ-DOWNLOAD`
- Tag: `baseline-from-main`
- User outcome: User downloads an assigned project without entering it immediately
- Preconditions: The main window is running and project actions are available from the Project menu.
- Trigger: `Project > Download` then select a project
- Expected visible result: Loading window and project selector appear; initialization runs without mounting the widget into the main window
- Expected persisted result: project directory, DB, state, and mode-specific assets are created under `data_dir/data/<project id>`
- Expected backend side effect: requests project list and downloads project artifacts
- Failure behavior: if the API is unreachable, the user gets an error dialog and download does not proceed
- Evidence refs: `main.py:MainWindow.download_project`; `annotation_widgets/factory.py:get_io`; mode-specific `download_project` implementations
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-DOWNLOAD-001`

### REQ-PROJ-REMOVE-001

- Workflow ID: `WF-PROJ-REMOVE`
- Tag: `baseline-from-main`
- User outcome: User removes a local project copy without changing server assignment
- Preconditions: The main window is running and project actions are available from the Project menu.
- Trigger: `Project > Remove project by ID` then confirm selection
- Expected visible result: selector opens with local or broken projects; success dialog appears; active widget closes if it matches the removed project
- Expected persisted result: local project directory is deleted recursively
- Expected backend side effect: none
- Failure behavior: broken local projects still appear when `with_broken_projects=True`; removal is local-only
- Evidence refs: `main.py:MainWindow.remove_project`; `path_manager.py:get_local_projects_data`; `path_manager.BasePathManager.project_path`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-REMOVE-001`

### REQ-PROJ-GOTO-001

- Workflow ID: `WF-PROJ-GOTO`
- Tag: `baseline-from-main`
- User outcome: User jumps directly to a numbered item inside an open widget
- Preconditions: The main window is running and project actions are available from the Project menu.
- Trigger: `Project > Go to ID` after a widget is active
- Expected visible result: ID form opens; widget switches to the requested item
- Expected persisted result: current item is saved before switching; item/state counters are persisted by widget logic
- Expected backend side effect: none
- Failure behavior: invalid or empty ID input leaves the current item unchanged
- Evidence refs: `main.py:MainWindow.go_to_id`; `annotation_widgets/widget.py:go_to_id`; `annotation_widgets/logic.py:go_to_id`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-GOTO-001`

### REQ-PROJ-RUNTIME-001

- Workflow ID: `WF-PROJ-RUNTIME`
- Tag: `baseline-from-main`
- User outcome: User can close, reopen, and resume a project with item position, processed items, and timing counters preserved
- Preconditions: The main window is running and project actions are available from the Project menu.
- Trigger: switch item, close a widget, reopen a local project, or complete a project
- Expected visible result: status bars resume from persisted counters and item position
- Expected persisted result: runtime values for `item_id`, `duration_hours`, and `processed_item_ids` are saved and restored; statistics logs append action/timing rows
- Expected backend side effect: statistics upload can occur during completion when a statistics file exists
- Failure behavior: invalid state or missing local DB makes the project invalid and forces redownload or broken-project fallback behavior
- Evidence refs: `annotation_widgets/logic.py:save_state`; `annotation_widgets/logic.py:load_state`; `annotation_widgets/logic.py:update_time_counter`; `annotation_widgets/io.py:complete_annotation`; `path_manager.BasePathManager.statistics_path`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-RUNTIME-001`

### REQ-PROJ-COMPLETE-001

- Workflow ID: `WF-PROJ-COMPLETE`
- Tag: `baseline-from-main`
- User outcome: User completes a project only after local save and pre-completion validation succeed
- Preconditions: The main window is running and project actions are available from the Project menu.
- Trigger: `Project > Complete the project` and confirm
- Expected visible result: confirmation dialog appears; success removes the active widget and resets the title to `Annotation tool`
- Expected persisted result: current item/state are saved first; counters reset; local stage is updated; local files may be removed after completion
- Expected backend side effect: uploads statistics and annotation outputs, then calls task completion API
- Failure behavior: if pre-check fails, show blocking error; if API is unreachable, completion is refused with an info dialog
- Evidence refs: `main.py:MainWindow.complete_project`; `annotation_widgets/widget.py:check_before_completion`; `annotation_widgets/io.py:complete_annotation`; mode-specific IO upload methods
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-COMPLETE-001`

### REQ-PROJ-UPDATE-001

- Workflow ID: `WF-PROJ-UPDATE`
- Tag: `baseline-from-main`
- User outcome: User pulls the current branch into the installed tool from the GUI
- Preconditions: The main window is running and project actions are available from the Project menu.
- Trigger: `Project > Update tool` and confirm
- Expected visible result: git pull output is shown in a message box; success message instructs the user to reopen the tool
- Expected persisted result: local git checkout updates in place
- Expected backend side effect: `git pull` against the repo remote
- Failure behavior: pull failures surface as raw stdout/stderr in the message box
- Evidence refs: `main.py:MainWindow.update_tool`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-UPDATE-001`

### REQ-HELP-HOW-001

- Workflow ID: `WF-HELP-HOW`
- Tag: `baseline-from-main`
- User outcome: User can read static usage instructions inside the app
- Preconditions: The main window is running and the Help menu is available.
- Trigger: `Help > How to use this tool?`
- Expected visible result: HTML help window opens
- Expected persisted result: none
- Expected backend side effect: none
- Failure behavior: missing template would raise file/open failure through the global exception handler
- Evidence refs: `main.py:MainWindow.show_how`; `templates/how.html`; `gui_utils.show_html_window`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-HELP-HOW-001`

### REQ-HELP-HOTKEYS-001

- Workflow ID: `WF-HELP-HOTKEYS`
- Tag: `baseline-from-main`
- User outcome: User can read static hotkey guidance inside the app
- Preconditions: The main window is running and the Help menu is available.
- Trigger: `Help > Hotkeys`
- Expected visible result: HTML hotkeys window opens
- Expected persisted result: none
- Expected backend side effect: none
- Failure behavior: missing template would raise file/open failure through the global exception handler
- Evidence refs: `main.py:MainWindow.show_hotkeys`; `templates/hotkeys.html`; `gui_utils.show_html_window`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-HELP-HOTKEYS-001`

### REQ-PROJ-SETTINGS-001

- Workflow ID: `WF-PROJ-SETTINGS`
- Tag: `baseline-from-main`
- User outcome: User can edit tool settings while the current widget schedules a refresh afterwards
- Preconditions: The main window is running and project actions are available from the Project menu.
- Trigger: `Project > Settings`
- Expected visible result: settings dialog opens over the current root window
- Expected persisted result: `settings.json` is rewritten; current widget schedules an update on exit
- Expected backend side effect: none
- Failure behavior: invalid settings remain guarded by the settings manager and app bootstrap checks
- Evidence refs: `main.py:MainWindow.open_settings`; `app.py:Application.__init__`; `config.py:Settings.save_settings`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-PROJ-SETTINGS-001`
- Invariant note: the stored settings shape must remain compatible with the default-settings merge behavior in `config.py`, where missing user values are filled from `DEFAULT_SETTINGS` rather than replacing the schema wholesale.

### REQ-CANV-VIEWPORT-001

- Workflow ID: `WF-CANV-VIEWPORT`
- Tag: `baseline-from-main`
- User outcome: Image-based workflows support zoom, pan, fit-to-window, and screen-to-image coordinate conversion
- Preconditions: An image-based project screen is open and the shared canvas has focus.
- Trigger: mouse wheel, right-button drag, resize, or `f` while an image canvas is active
- Expected visible result: viewport changes immediately and `fit_image()` resets scale and offsets on demand or item change when fit mode is active
- Expected persisted result: viewport state is runtime-only; figure coordinates are clamped to image bounds before handlers receive them
- Expected backend side effect: none
- Failure behavior: over-fast keyboard item switching is throttled by a minimum interval; coordinates are clamped to image edges
- Evidence refs: `annotation_widgets/image/widget.py:on_mouse_wheel`; `annotation_widgets/image/widget.py:fit_image`; `annotation_widgets/image/widget.py:scale_event_wrapper`; `annotation_widgets/image/widget.py:process_last_key_press`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-CANV-VIEWPORT-001`

### REQ-CANV-INPUT-001

- Workflow ID: `WF-CANV-INPUT`
- Tag: `baseline-from-main`
- User outcome: Image-based workflows route mouse and keyboard events through a shared canvas event loop
- Preconditions: An image-based project screen is open and the shared canvas has focus.
- Trigger: left/right mouse actions, hover, space, escape, navigation keys, and modifier keys while the canvas has focus
- Expected visible result: canvas redraws after hover, press, move, release, and key-driven navigation; shift toggles controller shift mode
- Expected persisted result: current item is saved on item switches; no extra persistence is created by hover-only redraws
- Expected backend side effect: none
- Failure behavior: repeated navigation faster than `min_time_between_frame_change` is ignored
- Evidence refs: `annotation_widgets/image/widget.py:handle_left_mouse_press`; `annotation_widgets/image/widget.py:handle_mouse_move`; `annotation_widgets/image/widget.py:handle_mouse_hover`; `annotation_widgets/image/widget.py:process_last_key_press`; `annotation_widgets/image/labeling/logic.py:on_shift_press`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-CANV-INPUT-001`

### REQ-CANV-RENDER-001

- Workflow ID: `WF-CANV-RENDER`
- Tag: `baseline-from-main`
- User outcome: Canvas render toggles change presentation without silently changing stored annotation geometry
- Preconditions: An image-based project screen is open and the shared canvas has focus.
- Trigger: visibility hotkeys, degraded preview toggle, blur figures, or overlay redraw
- Expected visible result: canvas redraws with hidden figures/review labels, blur regions, degraded preview, label names, object size, and overlay opacity rules
- Expected persisted result: display toggles are runtime-only; figure geometry persists separately
- Expected backend side effect: none
- Failure behavior: non-segmentation editing is blocked while figures are hidden; segmentation keeps the exception path
- Evidence refs: `annotation_widgets/image/labeling/logic.py:update_canvas`; `annotation_widgets/image/labeling/logic.py:switch_hiding_figures`; `annotation_widgets/image/labeling/logic.py:switch_hiding_review_labels`; `annotation_widgets/image/labeling/logic.py:switch_object_names_visibility`; `annotation_widgets/image/labeling/logic.py:switch_object_size_visibility`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-CANV-RENDER-001`

### REQ-FILT-SELECT-001

- Workflow ID: `WF-FILT-SELECT`
- Tag: `baseline-from-main`
- User outcome: Filtering user toggles the current frame as selected and sees that state immediately
- Preconditions: A filtering project is open and its video/session state has been initialized.
- Trigger: press `d` or `k` while filtering
- Expected visible result: green border appears or disappears; status bar selected counts update on next redraw
- Expected persisted result: `ClassificationImage.selected` is saved when the item changes or the widget closes
- Expected backend side effect: none until completion upload
- Failure behavior: selection only persists after `save_item` on switch/close/complete
- Evidence refs: `annotation_widgets/image/filtering/logic.py:select_image`; `annotation_widgets/image/filtering/logic.py:update_canvas`; `annotation_widgets/widget.py:close`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-FILT-SELECT-001`

### REQ-FILT-JUMP-001

- Workflow ID: `WF-FILT-JUMP`
- Tag: `baseline-from-main`
- User outcome: Filtering user jumps between previously selected frames
- Preconditions: A filtering project is open and its video/session state has been initialized.
- Trigger: press `z` for previous or `x` for next selected frame
- Expected visible result: current view switches to the nearest selected frame in the chosen direction
- Expected persisted result: current frame is saved before switching; item/state counters persist
- Expected backend side effect: none
- Failure behavior: if no earlier or later selected frame exists, the current frame remains unchanged
- Evidence refs: `annotation_widgets/image/filtering/logic.py:go_to_previous_selected`; `annotation_widgets/image/filtering/logic.py:go_to_next_selected`; `annotation_widgets/image/filtering/logic.py:switch_item`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-FILT-JUMP-001`

### REQ-FILT-DELAY-001

- Workflow ID: `WF-FILT-DELAY`
- Tag: `baseline-from-main`
- User outcome: Filtering user changes frame-step delay from the keyboard
- Preconditions: A filtering project is open and its video/session state has been initialized.
- Trigger: press `1`, `2`, `3`, or `4` while filtering
- Expected visible result: status bar delay text changes and frame stepping sleeps according to the selected preset
- Expected persisted result: none; delay is runtime-only
- Expected backend side effect: none
- Failure behavior: delay choice is not persisted across reopen
- Evidence refs: `annotation_widgets/image/filtering/logic.py:handle_key`; `annotation_widgets/image/filtering/logic.py:FilteringDelay`; `annotation_widgets/image/filtering/gui.py`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-FILT-DELAY-001`

### REQ-FILT-DATA-001

- Workflow ID: `WF-FILT-DATA`
- Tag: `baseline-from-main`
- User outcome: Filtering mode loads video frames and identifies items by decoded barcode name when available, else by frame index
- Preconditions: A filtering project is open and its video/session state has been initialized.
- Trigger: opening or downloading a filtering project
- Expected visible result: current frame becomes available for navigation and selection
- Expected persisted result: filtering repository stores item names and selected states; selected frames export later as JSON
- Expected backend side effect: project download and completion upload touch backend/file transfer paths
- Failure behavior: unreadable barcodes fall back to item ID identity instead of aborting the session
- Evidence refs: `annotation_widgets/image/filtering/io.py:download_project`; `annotation_widgets/image/filtering/logic.py:decode_img_name_from_image`; `annotation_widgets/image/filtering/logic.py:load_item`; `annotation_widgets/image/filtering/io.py:_upload_annotation_results`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-FILT-DATA-001`

### REQ-LABL-SWITCH-001

- Workflow ID: `WF-LABL-SWITCH`
- Tag: `baseline-from-main`
- User outcome: Labeling user moves between images with automatic save of the current image and state
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: navigation keys or `Go to ID` while a labeling widget is open
- Expected visible result: canvas reloads the next or requested image; status bar reflects the new item
- Expected persisted result: current figure/review-label edits and state counters are saved before the switch
- Expected backend side effect: none until overwrite or completion flows
- Failure behavior: out-of-range navigation is ignored after marking the current item as processed
- Evidence refs: `annotation_widgets/image/labeling/logic.py:save_item`; `annotation_widgets/image/labeling/logic.py:switch_item`; `annotation_widgets/widget.py:go_to_id`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-SWITCH-001`

### REQ-LABL-OVERWRITE-001

- Workflow ID: `WF-LABL-OVERWRITE`
- Tag: `baseline-from-main`
- User outcome: Labeling user can re-download annotations and replace local edits from the server
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: `Project > Download and overwrite annotations` from a labeling project
- Expected visible result: confirmation dialog and loading window appear; success dialog confirms overwrite
- Expected persisted result: local DB rows for labels, figures, review labels, and stage-specific flags are overwritten from downloaded files
- Expected backend side effect: downloads latest figures, review, and metadata files
- Failure behavior: API reachability is checked first; mismatched image/annotation counts raise an exception
- Evidence refs: `annotation_widgets/widget.py:overwrite_annotations`; `annotation_widgets/image/labeling/io.py:download_and_overwrite_annotations`; `annotation_widgets/image/labeling/io.py:overwrite_project`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-OVERWRITE-001`

### REQ-LABL-HELP-001

- Workflow ID: `WF-LABL-HELP`
- Tag: `baseline-from-main`
- User outcome: Labeling user can inspect figure classes and review labels from the Help menu
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: `Help > Classes` or `Help > Review Labels`
- Expected visible result: HTML window renders class metadata or review-label metadata
- Expected persisted result: none
- Expected backend side effect: none
- Failure behavior: missing templates or label data fail through the shared exception path
- Evidence refs: `annotation_widgets/image/widget.py:show_classes`; `annotation_widgets/image/labeling/widget.py:show_review_labels`; `annotation_widgets/image/labeling/widget.py:add_menu_items`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-HELP-001`

### REQ-LABL-CLASS-001

- Workflow ID: `WF-LABL-CLASS`
- Tag: `baseline-from-main`
- User outcome: Labeling user changes the active label by numeric hotkey or radial class selector
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: numeric keys or hold/release `a` over the canvas
- Expected visible result: active class changes; radial wheel shows labels, colors, and selected sector while open
- Expected persisted result: active-label choice is runtime-only until it affects an edit
- Expected backend side effect: none
- Failure behavior: editing is blocked from changing labels while figures are hidden in non-segmentation modes
- Evidence refs: `annotation_widgets/image/labeling/logic.py:change_label`; `annotation_widgets/image/labeling/logic.py:start_selecting_class`; `annotation_widgets/image/labeling/logic.py:end_selecting_class`; `annotation_widgets/image/drawing.py:create_class_selection_wheel`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-CLASS-001`

### REQ-LABL-HISTORY-001

- Workflow ID: `WF-LABL-HISTORY`
- Tag: `baseline-from-main`
- User outcome: Labeling user can delete, undo, redo, copy, paste, and copy from the previous image
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: `d`, `g`, `u`, Ctrl/Cmd shortcuts, or controller actions while editing
- Expected visible result: figure set changes immediately and redraws
- Expected persisted result: edited figure state persists when the current item is saved
- Expected backend side effect: none
- Failure behavior: history and edit commands are blocked when editing is blocked; paste/copy previous mark the item as changed
- Evidence refs: `annotation_widgets/image/widget.py:process_last_key_press`; `annotation_widgets/image/labeling/logic.py:delete_command`; `annotation_widgets/image/labeling/logic.py:undo`; `annotation_widgets/image/labeling/logic.py:redo`; `annotation_widgets/image/labeling/logic.py:copy_from_previous_image`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-HISTORY-001`

### REQ-LABL-TRASH-001

- Workflow ID: `WF-LABL-TRASH`
- Tag: `baseline-from-main`
- User outcome: Labeling workflow supports trash tagging and review-label behavior that depends on stage
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: press `t`, review-stage click actions, or stage-specific loading rules
- Expected visible result: trash status and review-label overlays update in the current item; review/correction stages filter the image subset
- Expected persisted result: trash persists on the labeled image; review labels persist in review data; correction/review subsets derive from stored review state
- Expected backend side effect: none until completion upload
- Failure behavior: trash toggling is ignored in review stage
- Evidence refs: `annotation_widgets/image/labeling/logic.py:toggle_image_trash_tag`; `annotation_widgets/image/labeling/logic.py:__init__`; `annotation_widgets/image/labeling/io.py:overwrite_project`; `annotation_widgets/image/labeling/widget.py:show_review_labels`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-TRASH-001`

### REQ-LABL-BBOX-001

- Workflow ID: `WF-LABL-BBOX`
- Tag: `baseline-from-main`
- User outcome: Object-detection projects support creating, selecting, moving, resizing, and deleting bounding boxes
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: bbox-mode mouse interactions and controller commands in a labeling project
- Expected visible result: bbox overlay updates on the canvas and participates in history/copy/paste flows
- Expected persisted result: bbox geometry persists with the current image on save
- Expected backend side effect: none until overwrite or completion flows
- Failure behavior: bbox editing obeys the same editing-blocked and save-boundary rules as other figure edits
- Evidence refs: `annotation_widgets/image/labeling/logic.py:handle_left_mouse_press`; `annotation_widgets/image/labeling/bboxes/models.py`; `annotation_widgets/image/labeling/figure_controller_factory.py`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-BBOX-001`

### REQ-LABL-MASK-001

- Workflow ID: `WF-LABL-MASK`
- Tag: `baseline-from-main`
- User outcome: Segmentation projects support creating and editing per-label masks with blur-aware rendering
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: segmentation-mode mouse interactions and controller commands in a labeling project
- Expected visible result: mask overlay updates on the canvas and participates in history/copy/paste flows
- Expected persisted result: mask RLE persists with the current image on save
- Expected backend side effect: none until overwrite or completion flows
- Failure behavior: segmentation keeps the hidden-figures editing exception path
- Evidence refs: `annotation_widgets/image/labeling/logic.py:handle_left_mouse_press`; `annotation_widgets/image/labeling/segmentation/figure_controller.py`; `annotation_widgets/image/labeling/segmentation/models.py`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-MASK-001`

### REQ-LABL-KPOINT-001

- Workflow ID: `WF-LABL-KPOINT`
- Tag: `baseline-from-main`
- User outcome: Keypoint projects support creating and editing grouped keypoints with label-defined attributes
- Preconditions: A labeling project is open with labels and image data loaded for the active stage.
- Trigger: keypoint-mode mouse interactions and controller commands in a labeling project
- Expected visible result: keypoint group overlay updates on the canvas and participates in history/copy/paste flows
- Expected persisted result: keypoint geometry and labels persist with the current image on save
- Expected backend side effect: none until overwrite or completion flows
- Failure behavior: keypoint edits obey the same save-boundary and editing-blocked rules as other figure edits
- Evidence refs: `annotation_widgets/image/labeling/logic.py:handle_left_mouse_press`; `annotation_widgets/image/labeling/keypoints/models.py`; `annotation_widgets/image/labeling/figure_controller_factory.py`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-LABL-KPOINT-001`

### REQ-EVAL-ANSWER-001

- Workflow ID: `WF-EVAL-ANSWER`
- Tag: `unknown`
- User outcome: Event-validation user records answers and comments per event item
- Preconditions: An event-validation project is open with questions and event data loaded.
- Trigger: choose answers in the sidebar or use numeric hotkeys; edit the comment field
- Expected visible result: sidebar state updates immediately
- Expected persisted result: answer/comment changes persist when the item is saved on switch, close, overwrite, or complete
- Expected backend side effect: none until completion upload
- Failure behavior: unsaved edits can still be lost if the process crashes before a save boundary
- Evidence refs: `annotation_widgets/event_validation/widget.py:save_answer`; `annotation_widgets/event_validation/widget.py:save_comment`; `annotation_widgets/event_validation/logic.py:update_answer`; `annotation_widgets/event_validation/logic.py:save_item`; `docs/product/workbook-crosswalk.md#workbook-coverage-gaps`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-EVAL-ANSWER-001`
- Authoring note: no dedicated event-validation workbook rows are mapped yet; this requirement is code-derived from `main` until the gap is resolved by crosswalk amendment or ADR.

### REQ-EVAL-VIEW-001

- Workflow ID: `WF-EVAL-VIEW`
- Tag: `unknown`
- User outcome: Event-validation user switches between video and image review modes and scrubs frames
- Preconditions: An event-validation project is open with questions and event data loaded.
- Trigger: press `a`, `s`, `z`, `x`, use slider, or play/pause controls
- Expected visible result: slider visibility and current frame update according to view mode; canvas redraws the selected frame or image
- Expected persisted result: current item answer/comment state persists only at save boundaries, not on frame scrubbing alone
- Expected backend side effect: none
- Failure behavior: image mode is forced off when the project has no image set; out-of-range frame loads are ignored
- Evidence refs: `annotation_widgets/event_validation/logic.py:change_view_mode`; `annotation_widgets/event_validation/logic.py:load_video_frame`; `annotation_widgets/event_validation/widget.py:on_slider_change`; `annotation_widgets/event_validation/widget.py:play_video`; `docs/product/workbook-crosswalk.md#workbook-coverage-gaps`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-EVAL-VIEW-001`
- Authoring note: no dedicated event-validation workbook rows are mapped yet; this requirement is code-derived from `main` until the gap is resolved by crosswalk amendment or ADR.

### REQ-EVAL-OVERWRITE-001

- Workflow ID: `WF-EVAL-OVERWRITE`
- Tag: `unknown`
- User outcome: Event-validation user can re-download validation answers and field definitions from the server
- Preconditions: An event-validation project is open with questions and event data loaded.
- Trigger: `Project > Download and overwrite annotations` from an event-validation project
- Expected visible result: overwrite runs and widget display refreshes from the rewritten event state
- Expected persisted result: stored fields and event answers/comments in the local DB are replaced from downloaded JSON
- Expected backend side effect: downloads event-validation results and metadata files
- Failure behavior: conflicting validation rules between saved results and meta fields raise an exception
- Evidence refs: `annotation_widgets/widget.py:overwrite_annotations`; `annotation_widgets/event_validation/io.py:download_and_overwrite_annotations`; `annotation_widgets/event_validation/io.py:overwrite_project`; `docs/product/workbook-crosswalk.md#workbook-coverage-gaps`
- Classification: intended behavior
- Decision owner: Product authority recorded in `docs/process/branch-strategy.md`
- Verification IDs: `V-EVAL-OVERWRITE-001`
- Authoring note: no dedicated event-validation workbook rows are mapped yet; this requirement is code-derived from `main` until the gap is resolved by crosswalk amendment or ADR.
