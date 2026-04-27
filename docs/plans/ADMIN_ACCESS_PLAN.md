# Admin Access Plan (Conservative Gate)

## What was added

- New module: `admin_access.py`
  - Adds `current_user_is_admin()`.
- Minimal UI integration point in `import_gui.pyw`:
  - `request_advanced_settings_access()` (not wired to a visible button/menu yet)
  - `_open_advanced_settings_placeholder()` for future use when admin access is granted.

## How admin detection works (high level)

- On Windows (`os.name == "nt"`), it calls `ctypes.windll.shell32.IsUserAnAdmin()`.
- On non-Windows platforms, it returns `False`.
- On any detection error/exception, it fails safe and returns `False`.

## Current UI wiring decision

- The current Tkinter UI has no existing Settings or Advanced Settings control/menu hook.
- To avoid awkward UI changes, no new visible button/menu was added.
- A clear future entry point now exists:
  - Call `request_advanced_settings_access()` from a future Settings/Advanced Settings action.

Behavior when that method is called:
- If admin check fails, show exactly:
  - `Admin login required to access advanced settings`
- If admin check passes, open a minimal placeholder dialog.

## Safety confirmation

- No XML generation logic changed.
- No case processing logic changed.
- No template selection behavior changed.
- No scan naming/routing/output naming/placeholder substitution/ID generation changed.
- No backend behavior changed outside the isolated admin-access gate.

## Limitations / known constraints

- Admin check is Windows-specific by design; non-Windows returns `False`.
- `IsUserAnAdmin()` reflects effective privileges of the running process; UAC/elevation context can affect result.
- The new gate method is intentionally not yet connected to visible UI controls.

