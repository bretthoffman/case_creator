# CASE CREATOR OPEN RULES FOLDER AUTOCREATE PATH REPORT

## 1. Summary of changes

Adjusted the Settings **Open Rules Folder** button behavior so it now ensures the live external rules folder path exists, then opens it.

Target path remains:

`%LOCALAPPDATA%\CaseCreator\business_rules\v1`

Behavior now:
- If already present: open in File Explorer (Windows).
- If missing: create only the missing folder path, then open it.

No rule seeding logic was changed.

## 2. Files modified

- `pyside6_ui.py`
- `tests/test_open_rules_folder_path.py`
- `CASE_CREATOR_OPEN_RULES_FOLDER_AUTOCREATE_PATH_REPORT.md` (this report)

## 3. UI/runtime behavior

In `pyside6_ui.py`:

- Existing button remains: **Open Rules Folder** in `SettingsDialog`.
- Added helper: `ensure_live_rules_folder_path_exists()`
  - Resolves `%LOCALAPPDATA%\CaseCreator\business_rules\v1`
  - Calls `os.makedirs(..., exist_ok=True)` for directory path only.
- Updated `_open_rules_folder()` to:
  1. Ensure folder path exists,
  2. Open it (`os.startfile` on Windows).

This handler does **not** create:
- `case_creator_rules.yaml`
- `CASE_CREATOR_RULES_EDIT_PROMPT.md`
- `README.md`

and does not touch first-run seed/business logic.

## 4. Validation performed

- Ran focused tests:
  - `python3 -m unittest tests.test_open_rules_folder_path -v`
  - Result: **2 passed**.

Covered checks:
- Path resolution still targets `%LOCALAPPDATA%\CaseCreator\business_rules\v1`.
- Missing path is created by helper.
- Created folder starts empty (no files auto-created inside).

- Lint diagnostics for changed files: **no linter errors**.

## 5. Remaining risks or limitations

- Actual Explorer-launch behavior is Windows-specific and should be manually smoke-tested on a Windows machine.
- If filesystem permissions deny creating `%LOCALAPPDATA%\CaseCreator\business_rules\v1`, button shows existing open-failure warning.

## 6. Recommended next step

On the target Windows machine:
1. Remove `%LOCALAPPDATA%\CaseCreator\business_rules\v1` if present.
2. Open Settings → click **Open Rules Folder**.
3. Confirm folder is created and opened.
4. Confirm no files are created in the folder.
5. Confirm normal Settings Save/Cancel flow remains unchanged.
