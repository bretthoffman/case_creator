# Packaging Hardening Plan (Settings Path Portability)

## What changed

Updated:
- `local_settings.py`
- `admin_settings.py`

Both now use a minimal mode-aware settings directory strategy.

## Settings location behavior

## Source/dev mode (non-frozen)

Behavior remains compatible with existing workflow:
- settings files resolve next to source modules (project directory):
  - `local_settings.json`
  - `admin_settings.json`

## Packaged/frozen mode on Windows

When running as a frozen app on Windows:
- settings files resolve to a stable writable per-user location:
  - `%LOCALAPPDATA%\CaseCreator\local_settings.json`
  - `%LOCALAPPDATA%\CaseCreator\admin_settings.json`

Directory handling:
- `%LOCALAPPDATA%\CaseCreator\` is created automatically on save if needed.

## Why this is safer for one-folder PyInstaller builds

- Avoids writing settings inside install/executable directories that may be read-only.
- Avoids tying settings persistence to app install path changes.
- Keeps per-user writable state in a standard Windows location.

## Why this is safer for future updater behavior

- App updates/reinstalls can replace app binaries without overwriting user settings.
- Settings survive path/version changes of the app folder.
- Reduces risk of settings-loss across updater rollouts.

## Tiny packaged-mode detection helper

A minimal helper was added in both modules:
- `_is_frozen_windows()` -> `os.name == "nt"` and `getattr(sys, "frozen", False)`

This is used only to choose settings directory; no processing behavior depends on it.

## Missing-file and save behavior

Unchanged safety characteristics:
- Missing/malformed settings files still fail safe to `{}`.
- Save still uses atomic write pattern (`.tmp` + `os.replace`).

## Backend safety confirmation

- No XML generation logic changed.
- No case processing logic changed.
- No template selection logic changed.
- No scan naming/routing/output naming/substitution/ID generation logic changed.

This pass is packaging-facing portability only.
