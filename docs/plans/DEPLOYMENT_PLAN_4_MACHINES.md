# Deployment Plan (4 Windows Machines)

This plan deploys the packaged PySide6 app conservatively to 4 machines, with rollback safety and no updater integration yet.

## 1) Deployment Artifacts to Copy

Source build output:
- `dist\CaseCreator\` (entire folder)

At minimum, each target machine needs:
- `CaseCreator.exe`
- all sibling files/subfolders produced in `dist\CaseCreator\` (do not cherry-pick files)

Recommendation:
- Copy the **entire `dist\CaseCreator\` folder as-is** to each machine.

## 2) Target Install Location (Suggested)

Use a consistent per-machine app folder, e.g.:
- `C:\Apps\CaseCreator\`

Then place packaged files under:
- `C:\Apps\CaseCreator\CaseCreator\...` (full copied folder contents)

Primary executable:
- `C:\Apps\CaseCreator\CaseCreator\CaseCreator.exe`

## 3) Settings Location

Packaged app settings path:
- `%LOCALAPPDATA%\CaseCreator\`

Files used there:
- `%LOCALAPPDATA%\CaseCreator\admin_settings.json`
- `%LOCALAPPDATA%\CaseCreator\local_settings.json`

## 4) `admin_settings.json` Placement

Per machine:
1. Ensure `%LOCALAPPDATA%\CaseCreator\` exists.
2. Copy prepared `admin_settings.json` into that folder.
3. Verify sensitive values are correct for that machine/site:
   - `EV_INT_BASE`
   - `EVO_USER`
   - `EVO_PASS`
   - `IMG_USER`
   - `IMG_PASS`

## 5) `local_settings.json` Creation Strategy

Use one of these conservative approaches:

### Option A (recommended): create through app UI
1. Launch app.
2. Open Normal Settings.
3. Set:
   - `EVIDENT_PATH`
   - `TRIOS_SCAN_ROOT`
   - `CC_IMPORTED_ROOT`
4. Save.
5. Confirm file exists at `%LOCALAPPDATA%\CaseCreator\local_settings.json`.

### Option B: pre-seed file manually
1. Prepare a validated `local_settings.json`.
2. Copy it to `%LOCALAPPDATA%\CaseCreator\`.
3. Launch app and verify values in Settings UI.

## 6) Per-Machine Setup Steps (Repeat x4)

1. **Pre-check**
   - Confirm machine can reach required mapped/network paths.
   - Confirm user account has access to `%LOCALAPPDATA%`.

2. **Deploy app files**
   - Copy full `dist\CaseCreator\` to target install location.

3. **Create shortcuts**
   - Desktop/start-menu shortcut target:
     - `...\CaseCreator.exe`

4. **Seed admin settings**
   - Place `admin_settings.json` in `%LOCALAPPDATA%\CaseCreator\`.

5. **Configure normal settings**
   - Launch app and set path fields in Normal Settings (or pre-seed local settings).

6. **Restart app**
   - Restart once after settings edits to ensure full path/config effect.

7. **Smoke test import**
   - Run one real test case import.
   - Confirm expected output appears in destination and imports into 3Shape.

8. **Operator handoff**
   - Confirm normal day-to-day launch path uses packaged `CaseCreator.exe`.

## 7) Post-Setup Test Checklist (Each Machine)

- App launches from packaged EXE.
- `%LOCALAPPDATA%\CaseCreator\admin_settings.json` exists and loads.
- `%LOCALAPPDATA%\CaseCreator\local_settings.json` exists (or is created on save).
- Normal Settings and Advanced Settings open and save without errors.
- Queue behavior works (2 quick case entries).
- Close guard works during active/queued import.
- One real import succeeds and appears correctly in 3Shape workflow.

## 8) Rollback Steps (Per Machine)

If packaged app has issues:

1. Stop using packaged shortcut on that machine.
2. Re-enable prior known-good fallback launch method for that machine.
3. Keep `%LOCALAPPDATA%\CaseCreator\` settings files for diagnostics.
4. Capture:
   - machine name
   - screenshot/error text
   - failing scenario
5. Fix/validate on one machine first, then redeploy to remaining machines.

## 9) Optional Deployment Helper

Use optional helper script:
- `deploy_casecreator_settings.bat`

It:
- creates `%LOCALAPPDATA%\CaseCreator` if missing,
- optionally copies `admin_settings.json` from a provided local source path.

## 10) What Comes Next After 4-Machine Deployment

1. **GitHub canonicalization**
   - ensure packaged PySide6 path and supporting scripts/docs are committed as canonical.
2. **Release workflow**
   - define versioning/tagging + repeatable build artifact process.
3. **Updater integration**
   - introduce WinSparkle/pywinsparkle only after stable packaged rollout baseline is confirmed.

This preserves a conservative sequence: stabilize deployment first, then automate update lifecycle.
