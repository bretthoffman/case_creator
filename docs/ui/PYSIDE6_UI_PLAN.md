# PySide6 UI Plan (Parallel First Pass)

## Proposed new UI file(s)

- `pyside6_ui.py`
  - First-pass parallel UI shell.
  - Runs independently from existing Tkinter UI.
  - Uses `import_service.py` as the only backend boundary for import workflow calls.

## Window structure (first pass)

- Main window with:
  - app title/version display (`get_app_info()`),
  - year selector,
  - case number input,
  - derived case ID preview,
  - `Import Case` button,
  - read-only log output area,
  - `Settings` button placeholder,
  - `Advanced Settings` button with admin gate.

## Action -> service mapping

- Case ID assembly:
  - `build_case_id(year, case_number)` from `import_service.py`
- Import trigger:
  - `import_case_by_id(case_id, log_callback=...)` from `import_service.py`
- Case ID validation:
  - `validate_case_id(case_id)` from `import_service.py`
- App metadata display:
  - `get_app_info()` from `import_service.py`
- Advanced Settings access gate:
  - `current_user_is_admin()` from `admin_access.py`

## Log display approach

- UI uses a read-only `QPlainTextEdit`.
- Import runs on a `QThread` worker to keep UI responsive.
- Backend log callback messages are appended directly to the log area.
- Error and finished states are surfaced in the same log area.

## Settings and Advanced Settings hooks

- `Settings` button:
  - placeholder dialog only in first pass.
- `Advanced Settings` button:
  - checks `current_user_is_admin()`.
  - if not admin, shows exactly:
    - `Admin login required to access advanced settings`
  - if admin, shows placeholder dialog (no settings implementation yet).

## What is intentionally NOT included in this first pass

- No replacement/removal of Tkinter UI.
- No backend refactor.
- No changes to XML/output logic.
- No settings persistence UI/editor yet.
- No packaging or installer updates.
- No update/self-update flow changes.
- No attempt to visually match current Tkinter theme exactly.

## Why this approach is low risk

- New UI is parallel and isolated.
- Frozen backend internals are untouched.
- Import path flows through a thin service wrapper (`import_service.py`), reducing direct coupling.
- Placeholder-only settings surfaces avoid accidental behavior changes.
- Existing Tkinter path remains available as known-good fallback.

## Relationship to current UI code

- Current Tkinter UI (`import_gui.pyw`) remains untouched.
- Current case-ID pattern (`year + "-" + stripped case number`) is mirrored through `import_service.build_case_id`.
- No broad UI refactor is performed in this step.

## Dependency note (conservative)

- `PySide6` is not currently listed in `requirements.txt`.
- For first-pass local testing, install separately:
  - `pip install PySide6`
- No packaging work was done in this step.

