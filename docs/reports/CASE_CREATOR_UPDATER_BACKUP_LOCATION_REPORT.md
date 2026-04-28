# CASE CREATOR UPDATER BACKUP LOCATION REPORT

## 1. Summary of changes

Updater backup folders were moved from `Documents`-adjacent naming (for example `C:\Users\<user>\Documents\CaseCreator.backup-...`) to a cleaner support path under Local AppData:

`%LOCALAPPDATA%\CaseCreator\update\backups\CaseCreator-YYYYMMDD-HHMMSS`

Rollback behavior is preserved and now references this new backup location.

## 2. Files modified

| File | Change |
|------|--------|
| `pyside6_ui.py` | In generated updater PowerShell: changed backup root derivation to `Join-Path $logDir "backups"` + timestamped `CaseCreator-...` child path; ensured backup directory creation with failure handling; added explicit backup base/path log lines. |
| `tests/test_updater_terminal_jokes_data.py` | Added assertions that generated script includes Local AppData backup path construction (`Join-Path $logDir "backups"` and `Join-Path $backupBase ("CaseCreator-" ... )`). |
| `docs/reports/CASE_CREATOR_UPDATER_BACKUP_LOCATION_REPORT.md` | This report. |

## 3. Old vs new backup behavior

- **Old:** Backup folder created beside install root in `Documents` (`CaseCreator.backup-...`).
- **New:** Backup folder created under `%LOCALAPPDATA%\CaseCreator\update\backups\CaseCreator-...`.
- **Unchanged:** Active install target remains `C:\Users\<user>\Documents\CaseCreator`.

## 4. Logging/runtime behavior

- Updater now logs:
  - `Backup base directory: %LOCALAPPDATA%\CaseCreator\update\backups`
  - `Backup path (if replace proceeds): ...\CaseCreator-YYYYMMDD-HHMMSS`
- Backup directory is created if missing (`New-Item -ItemType Directory -Force`).
- If directory creation fails, updater logs and exits with a clear fatal message.
- Rollback checks/moves still use `$backupRoot`, now pointing to the new Local AppData location.

## 5. Validation performed

- `python3 -m unittest tests.test_updater_terminal_jokes_data tests.test_updater_launch_workdir tests.test_updater_client_logging -v`
- Lint check on modified files reported no new issues.

## 6. Remaining risks or limitations

- This pass does not introduce backup retention/pruning; backups may accumulate under `%LOCALAPPDATA%\CaseCreator\update\backups`.
- Full end-to-end rollback behavior still depends on Windows filesystem state at runtime.

## 7. Recommended next step

Run a Windows updater pass and verify:
- no `CaseCreator.backup-*` appears in `Documents`,
- backup appears under `%LOCALAPPDATA%\CaseCreator\update\backups`,
- forced-failure rollback path restores install from the new backup location.
