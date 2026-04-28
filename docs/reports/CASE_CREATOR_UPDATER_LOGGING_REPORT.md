# CASE CREATOR UPDATER LOGGING REPORT

## 1. Summary of changes

The external PowerShell updater now appends structured, timestamped lines to a persistent log under `%LOCALAPPDATA%\CaseCreator\update\updater.log` for every major step (wait for main app, download, checksum, extract, layout validation, backup/swap, relaunch, rollback, final outcome). The main app writes `[client]` lines to the same file immediately before starting the updater (script path, job JSON path, install root, intended release, current version, PIDs) and on launch failures.

The updater is launched with a **new visible console window** (`CREATE_NEW_CONSOLE`) so progress and errors appear on screen during this debugging-oriented phase, in addition to the log file and existing error `MessageBox` calls.

If PowerShell exits almost immediately (syntax error, blocked execution, etc.), the UI now shows a warning with the log path instead of closing the app.

No business-rule semantics, release publishing, or install-root model were changed. User data under `%LOCALAPPDATA%\CaseCreator\` is still outside the replaced install tree.

## 2. Files modified

| File | Change |
|------|--------|
| `pyside6_ui.py` | Added `get_updater_state_dir`, `get_updater_log_path`, `append_updater_client_log`; expanded `_build_updater_powershell_script` with file logging and `Write-Host` steps; `launch_external_updater` now logs client lines, uses a visible console, returns `subprocess.Popen`; `UpdateCheckDialog` detects immediate updater exit and warns the user. |
| `tests/test_updater_client_logging.py` | New unit tests for log path resolution and append behavior. |
| `docs/reports/CASE_CREATOR_UPDATER_LOGGING_REPORT.md` | This report. |

## 3. Logging behavior

**Log file:** `%LOCALAPPDATA%\CaseCreator\update\updater.log` (UTF-8 lines appended over time).

**Client (Python) lines** — written from the main app:

- Single summary line before `Popen` with: updater script path, job file path, install root (`Documents\CaseCreator`), intended release (`latest_tag` / version), current app version, parent PID.
- Line after successful `Popen` with child PID.
- Lines on `Popen` failure or Python-side exceptions.
- Line if the updater process terminates within ~0.85s (immediate failure).

**Updater (PowerShell) lines** — prefixed with `[updater]` in the timestamped message:

- Launch start / log file path
- Job file path
- Wait for main app PID / wait finished
- Temp workspace paths
- Download start, success, or failure
- Checksum: start, OK, mismatch, failure, or skipped when no checksum URL
- Extract start, success, or failure
- Extracted structure validation OK or specific missing paths
- Install root and planned backup path
- Backup move success/failure or note when no prior install
- Install folder replacement success/failure
- Rollback attempts and success/failure when applicable
- Relaunch attempt success/failure
- `FINAL: success` or `FINAL: failure` after `FATAL:` detail on errors

## 4. Failure visibility improvements

- Visible PowerShell console for the updater process (debug phase).
- Persistent shared log for both client and updater.
- Message boxes retained on fatal updater paths.
- Immediate-exit detection avoids closing the app when the child process dies right away; user gets exit code and log path.
- Client-side exceptions when starting the updater are logged and shown in a warning dialog.

## 5. Validation performed

- `python -m unittest tests.test_updater_client_logging -v`
- Manual Windows validation is still recommended for full end-to-end update, download, and relaunch.

## 6. Remaining risks or limitations

- The short poll (~0.85s) for “immediate exit” is heuristic; an unusually slow machine could theoretically false-negative (rare).
- Updater success still depends on network, GitHub availability, disk space, AV/policy allowing `powershell.exe`, and correct release asset layout.
- The visible console is a deliberate tradeoff for observability; a future pass could gate it behind an env flag or settings toggle.

## 7. Recommended next step

Run a full Windows test from `C:\Users\<user>\Documents\CaseCreator`: **Check for Update → Update Now → Yes**, confirm the console shows progress, then open `%LOCALAPPDATA%\CaseCreator\update\updater.log` and verify step order and any failure `FATAL` lines match what happened.

---

## Final chat summary

1. **Persistent log:** Yes — the updater and the main app both append to `updater.log`.
2. **Location:** `%LOCALAPPDATA%\CaseCreator\update\updater.log`.
3. **Diagnosable on Windows:** Yes — combined file log, visible console, message boxes on fatal errors, and a client warning if PowerShell exits immediately.
4. **Retest end-to-end:** Yes — run the full update flow on a real Windows install to validate download, swap, relaunch, and log contents under production conditions.
