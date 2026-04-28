# CASE CREATOR UPDATER INSTALL PASS REPORT

## 1. Summary of changes

Implemented the first real update execution flow behind the existing **Check for Update** UX.

When an update is available and the user clicks **Update Now**:

1. Main app starts an **external PowerShell updater process**.
2. Main app exits.
3. Updater downloads the packaged release zip (and verifies checksum when `.sha256` is available).
4. Updater extracts and validates package structure.
5. Updater replaces install folder at `C:\Users\<user>\Documents\CaseCreator` via backup-and-swap.
6. Updater relaunches `CaseCreator.exe`.

No startup polling or auto-update-on-launch was added.

## 2. Files modified

- `pyside6_ui.py`
- `update_check.py`
- `tests/test_update_check.py`
- `CASE_CREATOR_UPDATER_INSTALL_PASS_REPORT.md` (this report)

## 3. Update flow

### UI flow

- Existing **Check for Update** dialog now enables an **Update Now** button when:
  - latest release is newer, and
  - a packaged release zip asset was found.
- Clicking **Update Now** prompts confirmation.
- On confirm:
  - app launches external updater process,
  - shows a brief confirmation message,
  - exits to allow replacement.

### External updater flow

`launch_external_updater(...)` writes:
- a job JSON (release URLs, install path, current PID),
- a generated PowerShell updater script,

then launches detached PowerShell:
- waits for current app PID to exit,
- downloads zip,
- optional checksum verification,
- extracts zip,
- validates `CaseCreator.exe` and `_internal`,
- backup/swap install root,
- relaunches `CaseCreator.exe`.

## 4. Install path and replace strategy

Install root is explicitly targeted as:
- `C:\Users\<user>\Documents\CaseCreator`

Replace strategy:
1. If install root exists, move to timestamped backup (`.backup-YYYYMMDD-HHMMSS`).
2. Move extracted `CaseCreator` folder into install root.
3. Relaunch new `CaseCreator.exe`.
4. On replacement/relaunch failure, attempt rollback from backup where practical.

## 5. Local AppData preservation behavior

Updater does **not** touch `%LOCALAPPDATA%\CaseCreator` paths.

No deletion/overwrite/reset of:
- `%LOCALAPPDATA%\CaseCreator\business_rules\v1\case_creator_rules.yaml`
- `%LOCALAPPDATA%\CaseCreator\local_settings.json`
- `%LOCALAPPDATA%\CaseCreator\admin_settings.json`

This pass only replaces the install folder under `Documents\CaseCreator`.

## 6. Release asset handling

From GitHub latest release metadata:
- selects packaged asset matching `CaseCreator-*-win64.zip`,
- ignores source archives (`source code.zip`, `source code.tar.gz`),
- captures optional `${zip}.sha256` URL.

Updater download behavior:
- always downloads selected packaged zip,
- verifies SHA256 when checksum asset exists,
- fails safely on mismatch.

## 7. Validation performed

### Automated tests

Ran:
- `python3 -m unittest tests.test_update_check tests.test_open_rules_folder_path -v`

Result:
- **9 tests passed**.

Covered:
- update available / up-to-date / failure paths,
- repo override behavior,
- release asset selection ignoring source archives,
- existing settings rules-folder path tests unaffected.

### Static checks

- Linter diagnostics on changed files: **no issues**.

### Manual validation required on Windows (not executable in this environment)

Still required to verify end-to-end:
- app exit before replacement,
- real download/extract/swap on `Documents\CaseCreator`,
- relaunch behavior,
- rollback behavior under forced failure scenarios.

## 8. Risks or limitations

- Updater is script-based (PowerShell) rather than a dedicated signed helper EXE.
- Windows filesystem/permissions/AV can still interfere with folder moves in some environments.
- Backup cleanup policy is not yet automated (backup retained).
- UI currently shows simple status text, not detailed progress logs.

## 9. Recommended next step

Safest next pass:
1. Run full Windows manual validation matrix (success + failure/rollback scenarios).
2. Add explicit structured updater logging file for support diagnostics.
3. Optionally move from generated PowerShell script to a packaged dedicated updater helper EXE/script artifact for stronger operational stability.
