# Production-Safe Rehearsal Lane - 2026-04-23

This procedure is the safe subset of the Linux release rehearsal when the configured backend is production and project state must not be updated or completed.

## Intent

Allowed:

- local-only migration rehearsal on a copied Tk-era project directory
- local-only rollback rehearsal after a PySide write
- local filesystem inspection
- local app launch

Not allowed in this lane:

- project download from production
- overwrite-from-backend against production
- project completion or upload
- any workflow that intentionally mutates backend task state

## Why This Extra Lane Exists

Two PySide code paths are explicitly unsafe for a production-safe rehearsal:

- completion uploads result files and calls backend task completion in `annotation_tool/services/completion_service.py`
- normal project open first tries the backend project list in `annotation_tool/services/project_service.py`

Because of that, the safe approach is:

1. use a copied local project directory only
2. force backend access to fail fast
3. let both apps fall back to local-project behavior

## What This Lane Proves

This lane can still prove the highest-risk technical claims:

- Tk project directory can be opened locally in Tk
- same copied directory can be opened in PySide
- PySide migrators seed `cache.json` and `runtime_state.json`
- `db.sqlite` stays unchanged by migration
- post-PySide-write rollback behavior matches documented policy

This lane does **not** prove:

- fresh download from backend
- completion upload
- in-app production update acceptance

## Required Inputs

- one copied non-EV Tk-era project directory
- one Linux workstation with GUI access
- Tk baseline repo: `/home/yehor/Work/annotation_tool`
- PySide repo: `/home/yehor/Work/annotation_tool-pyside-audit`

## Temporary Rehearsal Paths

Recommended paths:

```text
/tmp/pyside-prod-safe/pristine/<PROJECT_DIR>
/tmp/pyside-prod-safe/data
/tmp/pyside-prod-safe/post-pyside-write
```

## Settings Files To Touch

Tk settings file:

```text
/home/yehor/Work/annotation_tool/settings.json
```

PySide settings file:

```text
/home/yehor/Work/annotation_tool-pyside-audit/settings.json
```

Before editing either one, back them up:

```bash
cp /home/yehor/Work/annotation_tool/settings.json /tmp/tk-settings.backup.json
cp /home/yehor/Work/annotation_tool-pyside-audit/settings.json /tmp/pyside-settings.backup.json
```

## Safe Offline Settings Strategy

The apps require non-empty `token`, `api_url`, `file_url`, and `data_dir`, but they do not require those URLs to be valid.

Use temporary settings that are syntactically non-empty but intentionally unreachable:

- `token = production-token-placeholder`
- `api_url = http://127.0.0.1:9`
- `file_url = http://127.0.0.1:9`
- `data_dir = /tmp/pyside-prod-safe`

Port `9` is the discard service and will fail immediately on most systems. That gives a fast backend failure instead of an accidental production call.

## Prepare Rehearsal Data

```bash
mkdir -p /tmp/pyside-prod-safe/data/data
mkdir -p /tmp/pyside-prod-safe/post-pyside-write
cp -r <PRISTINE_PROJECT_DIR> /tmp/pyside-prod-safe/data/data/<ZERO_PADDED_PROJECT_ID>
```

## Step 1 - Configure Tk For Local-Only Open

Edit `/home/yehor/Work/annotation_tool/settings.json` so that:

- `general.token.value` is non-empty
- `general.api_url.value` is `http://127.0.0.1:9`
- `general.file_url.value` is `http://127.0.0.1:9`
- `general.data_dir.value` is `/tmp/pyside-prod-safe`

Then:

```bash
cd /home/yehor/Work/annotation_tool
git checkout 1dd11801066386f137f64ab2ad028005f325f463
bash install_linux.sh
source venv/bin/activate
python3 app.py
```

In Tk:

1. Use `Project > Open`.
2. The backend lookup should fail and the app should fall back to local projects.
3. Open the copied project only.
4. Record:
   - current item
   - duration
   - one visible label
   - one visible figure or selected frame state
5. Close Tk cleanly.

Record SQLite mtime:

```bash
stat /tmp/pyside-prod-safe/data/<ZERO_PADDED_PROJECT_ID>/db.sqlite
```

## Step 2 - Configure PySide For Local-Only Open

Edit `/home/yehor/Work/annotation_tool-pyside-audit/settings.json` with the same temporary values:

- token
- `api_url = http://127.0.0.1:9`
- `file_url = http://127.0.0.1:9`
- `data_dir = /tmp/pyside-prod-safe`

Then:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
git checkout pyside-fr-audit
bash install_linux.sh
source venv/bin/activate
python -m annotation_tool
```

In PySide:

1. Use `Project > Open`.
2. Backend lookup should fail and the app should fall back to local projects.
3. Open the same copied project.
4. Verify:
   - current item matches Tk
   - duration is continuous
   - labels are present
   - at least one figure migrated correctly
5. Confirm new files exist:
   - `cache.json`
   - `runtime_state.json`
6. Confirm `db.sqlite` mtime is unchanged.
7. Add one local annotation or selection.
8. Move forward one item.
9. Close PySide cleanly.

File checks:

```bash
ls -l /tmp/pyside-prod-safe/data/<ZERO_PADDED_PROJECT_ID>
stat /tmp/pyside-prod-safe/data/<ZERO_PADDED_PROJECT_ID>/db.sqlite
```

## Step 3 - Roll Back To Tk

Snapshot the post-PySide-write project:

```bash
cp -r /tmp/pyside-prod-safe/data/<ZERO_PADDED_PROJECT_ID> /tmp/pyside-prod-safe/post-pyside-write/
```

Return to Tk:

```bash
cd /home/yehor/Work/annotation_tool
git checkout 1dd11801066386f137f64ab2ad028005f325f463
bash install_linux.sh
source venv/bin/activate
python3 app.py
```

In Tk:

1. Use `Project > Open` again.
2. Let it fall back to local projects.
3. Open the same copied project.
4. Record which documented rollback outcome occurs:
   - safe reopen at pre-PySide visible state
   - or explicit block

SQLite check:

```bash
sqlite3 /tmp/pyside-prod-safe/data/<ZERO_PADDED_PROJECT_ID>/db.sqlite '.schema'
```

## Pass Criteria For This Lane

- no production API or file-service calls succeed
- copied project opens locally in Tk
- copied project opens locally in PySide
- migrator creates `cache.json` and `runtime_state.json`
- `db.sqlite` remains unchanged during migration
- Tk rollback is safe or explicitly blocked

## Explicitly Deferred In This Lane

Run these later in staging or another non-production-safe environment:

- fresh download drill
- completion or upload drill
- overwrite-from-backend drill
- any confirmation or completion action against a real backend task

## Cleanup

Restore the original settings files after the rehearsal:

```bash
cp /tmp/tk-settings.backup.json /home/yehor/Work/annotation_tool/settings.json
cp /tmp/pyside-settings.backup.json /home/yehor/Work/annotation_tool-pyside-audit/settings.json
```

If one of the settings files did not exist before rehearsal, remove it instead of restoring it.
