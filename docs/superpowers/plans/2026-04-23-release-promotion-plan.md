# PySide Linux Release Promotion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce promotion-grade evidence that the PySide candidate can replace the Tk build for the approved first-release Linux scope.

**Architecture:** Treat this as an evidence and release-readiness plan, not a feature plan. Keep the existing code and scope decisions intact, execute the documented rehearsal drills against the pinned repos, then update the quality docs only with verified outcomes from those drills.

**Tech Stack:** PySide6, pytest, git, Linux desktop environment, local filesystem rehearsal data, annotation backend credentials when using the non-safe lane.

---

### Approved Track

- [x] Use the promotion-minimum track rather than reopening feature scope.
- [x] Treat headless backend/download/open/reopen evidence as sufficient for reachability and persistence confidence.
- [ ] Keep the remaining gate focused on manual visual parity, explicit rollback confirmation, and safe-environment backend-sensitive drills.

### Current Evidence Status

- [x] PySide pytest lane re-run on 2026-04-24: `139 passed in 1.07s`
- [x] Live backend visibility confirmed for both target projects:
  - `8071` `OBJECT_DETECTION` `ANNOTATE`
  - `21852` `FILTERING` `FILTERING`
- [x] Live `download_project()` path verified for both projects into `/home/yehor/Data/labeling`
- [x] Live headless open -> navigate -> close -> reopen verified for both projects
- [x] `db.sqlite` stayed unchanged during the live open/reopen cycles for both projects
- [x] Stable local-only migration proof exists for copied `08071`
- [x] Tk reopen after PySide JSON writes has been demonstrated on copied `08071`

### Task 1: Capture preflight state

**Files:**
- Create: `docs/quality/linux-release-rehearsal-log-2026-04-23.md`
- Read: `docs/quality/linux-release-rehearsal-runbook-2026-04-23.md`
- Read: `docs/quality/pyside-release-readiness-2026-04-23.md`

- [ ] **Step 1: Record pinned repo revisions and worktree state**

Run:

```bash
git -C /home/yehor/Work/annotation_tool rev-parse HEAD
git -C /home/yehor/Work/annotation_tool-pyside-audit rev-parse HEAD
git -C /home/yehor/Work/annotation_tool status --short --branch
git -C /home/yehor/Work/annotation_tool-pyside-audit status --short --branch
```

Expected:

- Tk repo at `1dd11801066386f137f64ab2ad028005f325f463`
- PySide repo at `5f58ac5822b599b7c975474351954a4b14c118c0`
- any local untracked files explicitly listed in the rehearsal log

- [ ] **Step 2: Re-run the documented automated baseline**

Run:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
PYTHONPATH=. QT_QPA_PLATFORM=offscreen venv/bin/pytest -q
```

Expected:

- green run
- current observed result recorded verbatim in the rehearsal log

- [ ] **Step 3: Create the rehearsal log document**

Use this initial content:

```markdown
# Linux Release Rehearsal Log - 2026-04-23

## Operator

- Executor:
- Linux machine:
- Backend environment:
- Reference project ID:
- Reference project mode:

## Preflight

- Tk commit:
- PySide commit:
- Tk git status:
- PySide git status:
- PySide pytest result:

## Drill Results

### Drill 1 - Upgrade Tk -> PySide

- Status:
- Notes:

### Drill 2 - Rollback After PySide Write

- Status:
- Notes:

### Drill 3 - Fresh Install

- Status:
- Notes:

### Drill 4 - In-App Update Tool

- Status:
- Notes:

## Final Verdict

- Promotion recommendation:
- Blocking issues:
```

- [ ] **Step 4: Commit the log scaffold if the repo owner wants rehearsal evidence kept in-tree**

Run:

```bash
git add docs/quality/linux-release-rehearsal-log-2026-04-23.md
git commit -m "docs: add linux release rehearsal log scaffold"
```

Expected:

- one docs-only commit with no runtime code changes

### Task 2: Choose the correct rehearsal lane

**Files:**
- Read: `docs/quality/linux-release-rehearsal-runbook-2026-04-23.md`
- Read: `docs/quality/production-safe-rehearsal-lane-2026-04-23.md`
- Modify: `docs/quality/linux-release-rehearsal-log-2026-04-23.md`

- [ ] **Step 1: Decide whether the backend environment allows state mutation**

Decision rule:

- use the full runbook when staging or another safe non-production environment is available
- use the production-safe lane when the configured backend is production or uncertain

- [ ] **Step 2: Record the chosen lane and rationale in the log**

Use one of these entries:

```markdown
- Chosen lane: full Linux release rehearsal
- Reason: non-production backend available; download, completion, and update acceptance can be exercised safely
```

or

```markdown
- Chosen lane: production-safe local-only rehearsal
- Reason: production or uncertain backend; only local migration and rollback proof is allowed
```

- [ ] **Step 3: Stop if the required operator inputs are missing**

Required inputs:

- one real non-EV project directory
- pristine backup path
- chosen temporary `data_dir`
- GUI-capable Linux workstation
- backend credentials only if the full lane is selected

- [ ] **Step 4: Commit the lane decision only if the repo owner wants an in-tree evidence trail**

Run:

```bash
git add docs/quality/linux-release-rehearsal-log-2026-04-23.md
git commit -m "docs: record rehearsal lane decision"
```

Expected:

- docs-only change with the selected lane recorded

### Task 3: Close the remaining promotion-minimum gate

**Files:**
- Modify: `docs/quality/linux-release-rehearsal-log-2026-04-23.md`
- Read: `docs/quality/linux-release-rehearsal-runbook-2026-04-23.md`
- Read: `docs/quality/production-safe-rehearsal-lane-2026-04-23.md`

- [ ] **Step 1: Prepare the rehearsal workspace**

Run the human-reviewed visual comparison on the currently verified live projects:

- `08071` for detection
- `21852` for filtering

Expected:

- Tk and PySide both open the same working copies
- operator records visible current item, duration, one label or figure state, and one filtering frame state where applicable
- any visual mismatch is logged explicitly

- [ ] **Step 2: Record one explicit Tk rollback-after-PySide-write result**

Run:

```bash
cd /home/yehor/Work/annotation_tool
source venv/bin/activate
python3 app.py
```

Expected:

- Tk either reopens the PySide-touched working copy safely or blocks explicitly
- no crash
- outcome recorded with project ID and concrete visible behavior

- [ ] **Step 3: Execute backend-sensitive acceptance in a safe environment**

Run:

```bash
python -m annotation_tool
```

Expected:

- fresh install -> configure -> download -> annotate -> reopen -> complete or upload succeeds
- in-app `Project -> Update tool` succeeds from an older PySide revision
- commands, commits, and operator observations are recorded in the rehearsal log

- [ ] **Step 4: Promote if the remaining gate passes**

Expected:

- quality docs updated to promotion-ready status
- PySide described as ready for the approved Linux first-release scope
- SQLite schema remains readable

- [ ] **Step 6: Commit the log update if the drill produced useful evidence**

Run:

```bash
git add docs/quality/linux-release-rehearsal-log-2026-04-23.md
git commit -m "docs: record migration and rollback rehearsal results"
```

Expected:

- docs-only evidence commit

### Task 4: Execute Drill 3 and Drill 4 in a safe backend environment

**Files:**
- Modify: `docs/quality/linux-release-rehearsal-log-2026-04-23.md`
- Modify: `docs/quality/pyside-release-readiness-2026-04-23.md`

- [ ] **Step 1: Run the fresh-install drill on a clean PySide environment**

Run:

```bash
rm -rf /tmp/pyside-fresh-install-data
mkdir -p /tmp/pyside-fresh-install-data
cd /home/yehor/Work/annotation_tool-pyside-audit
git checkout pyside-fr-audit
bash install_linux.sh
source venv/bin/activate
python -m annotation_tool
```

Expected:

- first-launch settings flow appears
- download, open, edit, reopen, and complete succeed for one non-EV project

- [ ] **Step 2: Run the in-app update drill from an older PySide revision**

Run before launch:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
git rev-parse HEAD
git status --short
```

Then use the GUI `Project -> Update tool`, relaunch, and record:

```bash
cd /home/yehor/Work/annotation_tool-pyside-audit
git rev-parse HEAD
git status --short
```

Expected:

- update dialog shows git output and reopen guidance
- app relaunches
- worktree is clean after update

- [ ] **Step 3: Update the readiness verdict only after all drills pass**

Apply this change to `docs/quality/pyside-release-readiness-2026-04-23.md`:

```markdown
The Linux release rehearsal has been executed and recorded in `docs/quality/linux-release-rehearsal-log-2026-04-23.md`.

PySide is ready to replace Tk for supported Linux users within the approved first-release scope.
```

- [ ] **Step 4: Commit the readiness verdict update**

Run:

```bash
git add docs/quality/linux-release-rehearsal-log-2026-04-23.md docs/quality/pyside-release-readiness-2026-04-23.md
git commit -m "docs: promote pyside after linux rehearsal"
```

Expected:

- promotion verdict is backed by a completed rehearsal log

### Task 5: Post-promotion development backlog

**Files:**
- Modify: `docs/quality/pyside-release-readiness-2026-04-23.md`
- Modify: `docs/quality/pyside-test-disposition.md`
- Modify: `docs/product/workbook-crosswalk.md`

- [ ] **Step 1: Track the first explicit post-promotion gap**

Gap:

```text
FR-145: status-bar font adapts to window width
```

Expected:

- remains deferred until a headful resize harness exists

- [ ] **Step 2: Keep event validation in the backlog as deferred parity work**

Backlog scope:

```text
WF-EVAL-ANSWER
WF-EVAL-VIEW
WF-EVAL-OVERWRITE
REQ-EVAL-ANSWER-001
REQ-EVAL-VIEW-001
REQ-EVAL-OVERWRITE-001
```

Expected:

- no accidental scope creep into the first-release promotion branch

- [ ] **Step 3: Harden non-proof-grade tests after promotion**

Priority files:

```text
tests/test_project_management.py
tests/test_project_completion.py
tests/test_annotation_import.py
tests/test_annotation_export.py
tests/test_installation_and_update.py
```

Expected:

- move `rewrite-or-augment` and `review-before-accept` coverage toward proof-grade parity evidence

- [ ] **Step 4: Commit backlog doc updates only after scope owners agree**

Run:

```bash
git add docs/quality/pyside-release-readiness-2026-04-23.md docs/quality/pyside-test-disposition.md docs/product/workbook-crosswalk.md
git commit -m "docs: record post-promotion parity backlog"
```

Expected:

- backlog remains explicit and separated from the shipped Linux release scope
