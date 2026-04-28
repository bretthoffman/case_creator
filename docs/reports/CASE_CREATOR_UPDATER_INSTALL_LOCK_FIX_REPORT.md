# CASE CREATOR UPDATER INSTALL LOCK FIX REPORT

## 1. Summary of changes

The updater no longer inherits the main app’s current working directory when PowerShell starts (`subprocess.Popen(..., cwd=runner_dir)`), and the script immediately `Set-Location`s to the directory that contains `case_creator_updater.ps1` (under `%TEMP%\CaseCreatorUpdater\`), so the updater process does not keep a handle on `Documents\CaseCreator`.

After the main app PID wait, the script waits **2 seconds** before any move, then performs **backup** and **install** moves with **`Move-Item` retries** (12 attempts, 800 ms between attempts), logging each attempt and the active working directory. Fatal backup failures that look like file locks include a short operator hint. Rollback paths are unchanged in intent.

## 2. Files modified

| File | Change |
|------|--------|
| `pyside6_ui.py` | `launch_external_updater`: `cwd=runner_dir`; client log includes `subprocess_cwd`. Embedded updater script: log script path, initial CWD, CWD after chdir; clearer PID wait outcome; 2s stabilization delay; `Move-Item-WithRetry` for backup and install moves; lock-oriented error hint. |
| `tests/test_updater_launch_workdir.py` | New test: `Popen` `cwd` is under temp runner dir, not `Documents\CaseCreator`. |

Report path: `docs/reports/CASE_CREATOR_UPDATER_INSTALL_LOCK_FIX_REPORT.md` (project convention for pass reports).

## 3. Root cause

On Windows, a process **current directory** is often a **directory handle** on that folder. Case Creator runs from `C:\Users\<user>\Documents\CaseCreator`. The updater was launched without an explicit `cwd`, so **PowerShell inherited that directory**. After the UI exited, the **updater process still had the install folder as its CWD**, so `Move-Item` on that path failed with “cannot move … in use” even though the main app PID had ended.

## 4. Fix applied

1. **Python:** `subprocess.Popen(..., cwd=runner_dir)` so the child’s initial CWD is `%TEMP%\CaseCreatorUpdater` (same tree as the `.ps1` / job JSON — not the install root).

2. **PowerShell:** Log `$PSCommandPath` and initial `Get-Location`, then `Set-Location` to the script’s parent directory.

3. **Timing:** Fixed PID-wait logging; **2 s sleep** after wait loop before touching the install tree.

4. **Retries:** Shared `Move-Item-WithRetry` for backup rename and for moving the extracted `CaseCreator` folder into place, with per-attempt log lines.

5. **UX:** If the backup move still fails with typical “in use / access” wording, append a short hint about Explorer, AV, and retry.

`%LOCALAPPDATA%\CaseCreator\` rule files were not altered; only existing `update\updater.log` append behavior continues as before.

## 5. Validation performed

- `python3 -m unittest tests.test_updater_launch_workdir tests.test_updater_client_logging -v`
- Full Windows end-to-end update should still be run on a real machine.

## 6. Remaining risks or limitations

- **Explorer** or **antivirus** can still hold the install folder; retries reduce but do not eliminate that.
- If the main app PID never exits within ~45 s, the log warns and moves may still fail.
- Other processes launched from the install folder could lock files; this pass does not enumerate or stop them.

## 7. Recommended next step

Re-run **Check for Update → Update Now** on Windows from `Documents\CaseCreator`, confirm `updater.log` shows script path, CWD change, stabilization delay, and `[backup-move]` / `[install-move]` attempt lines, and confirm the backup rename succeeds.

---

## Final chat summary

1. **Runs from outside install folder:** Yes — `cwd` is the temp runner dir and the script chdirs to the script directory (not `Documents\CaseCreator`).
2. **Move step retries:** Yes — backup and install folder moves use up to 12 attempts with 800 ms spacing.
3. **Logging improved:** Yes — script path, initial and updated CWD, PID wait outcome, post-exit delay, and each move attempt (with CWD) are logged; client log includes `subprocess_cwd`.
4. **Retest on Windows:** Yes — required to confirm behavior under real locks (Explorer, AV).
