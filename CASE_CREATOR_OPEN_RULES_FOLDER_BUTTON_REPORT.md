# CASE CREATOR OPEN RULES FOLDER BUTTON REPORT

## 1. Summary of changes

Added a new **Settings** dialog button labeled **Open Rules Folder**.

When clicked, it now resolves the live external rules folder path:

`%LOCALAPPDATA%\CaseCreator\business_rules\v1`

Behavior:
- If folder exists: opens it (Windows: File Explorer via `os.startfile`).
- If folder missing: shows user message **"Cannot find rules folder."**
- No folder creation, no seeding, no business-logic changes.

## 2. Files modified

- `pyside6_ui.py`
- `tests/test_open_rules_folder_path.py` (new)
- `CASE_CREATOR_OPEN_RULES_FOLDER_BUTTON_REPORT.md` (this report)

## 3. UI change

In `SettingsDialog` (`pyside6_ui.py`):
- Added `QPushButton("Open Rules Folder")` in the existing Settings layout, just above the Save/Cancel buttons.
- Hooked it to a new `_open_rules_folder()` handler.

Also added a small helper:
- `get_live_rules_folder_path()` -> returns `LOCALAPPDATA/CaseCreator/business_rules/v1`.

## 4. Runtime behavior

`_open_rules_folder()` now:
1. Computes live folder path using `get_live_rules_folder_path()`.
2. Checks existence with `os.path.isdir()`.
3. If missing: `QMessageBox.information(..., "Cannot find rules folder.")`.
4. If present on Windows: opens with `os.startfile(folder)`.
5. Does **not** call `os.makedirs`, does **not** seed files, and does **not** open repo/seed paths.

## 5. Validation performed

- Added and ran unit test:
  - `python3 -m unittest tests.test_open_rules_folder_path -v`
  - **Passed**.
- Lint/diagnostics check on changed files: **no linter errors**.
- Code-path review confirms this button does not create directories or modify settings save behavior.

## 6. Remaining risks or limitations

- The full click-path UI behavior (actual Explorer launch and missing-folder dialog) requires manual verification on the Windows packaged app runtime.
- On non-Windows hosts, the handler shows the resolved path message instead of launching File Explorer (Windows behavior is the target for this feature).

## 7. Recommended next step

Run a quick Windows manual smoke test:
1. Open Settings and verify **Open Rules Folder** button is visible.
2. With folder present, click and confirm Explorer opens `%LOCALAPPDATA%\CaseCreator\business_rules\v1`.
3. Temporarily rename/remove `business_rules\v1` and confirm button shows **"Cannot find rules folder."** and does not recreate it.
4. Confirm normal Save/Cancel settings flow still works unchanged.
