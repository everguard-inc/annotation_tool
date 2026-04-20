# Annotation Tool

Desktop application for image annotation, review, segmentation, keypoints annotation, and frame filtering projects.

The application downloads assigned projects from the annotation backend, stores project data locally, lets users annotate or review items, and uploads results when a project is completed.

## Main features

- Open assigned annotation projects from the backend.
- Continue already downloaded projects when the backend is unavailable.
- Annotate object detection projects with bounding boxes.
- Annotate keypoint projects using class keypoint templates.
- Annotate segmentation projects using polygon masks.
- Review projects using review labels.
- Filter video frames and export selected frame names or IDs.
- Save local runtime state and progress.
- Show Help, Hotkeys, Classes, and Review Labels pages.
- Show uncaught errors in a copyable error window with traceback for support.

## Requirements

- Linux
- Python 3.10+
- Git
- Access to the annotation backend and file service

## Installation

Clone or unpack the project, open terminal in the project directory, then run:

```bash
bash install_linux.sh
````

The installer will:

* install required Ubuntu packages;
* create `venv`;
* install Python dependencies from `requirements.txt`;
* create a desktop shortcut named `Labeling.desktop`.

After installation, run the app from the desktop shortcut.

If Ubuntu blocks launching the shortcut, right click `Labeling.desktop` on Desktop and choose `Allow Launching`.

## Settings

The application creates `settings.json` automatically on first launch.

If required settings are missing, the app opens a settings window and asks the user to fill in:

- token
- API URL
- file URL
- data directory

The settings window can also be opened later from `Project > Settings`.

If the required settings are not filled in, pressing `Cancel and exit` or closing the settings window exits the application.

## Running manually

```bash
source venv/bin/activate
python -m annotation_tool
```

## Updating

Use `Project > Update tool`.

The update action runs:

```bash
git pull
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

It also refreshes the desktop shortcut so users can reopen the updated PySide6 version from the same icon.

After update, close the app and open it again from the desktop shortcut.

## Usage

Use the `Project` menu to open, download, remove, update, or complete projects.

Use the `Help` menu to open:

* How to use this tool
* Hotkeys
* Classes
* Review Labels

## Support and debugging

If an unexpected error happens, the application shows a window with a traceback. Copy the full traceback and send it to technical support together with the project ID and a short description of what you were doing.