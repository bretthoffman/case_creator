# Local Settings First-Run Check

This is a conservative verification of behavior when `local_settings.json` is missing.

## 1) Launch safety when `local_settings.json` is absent

**Result: safe.**

Why:
- `local_settings.load_local_settings()` catches `FileNotFoundError` and returns `{}`.
- `local_settings.get_setting(key, default)` then uses provided defaults.
- `config.py` uses `get_setting(...)` with hardcoded/default fallback values for all local-overridable keys.

So missing file does not block startup.

## 2) Values that fall back safely when file is absent

From `config.py`, these local-overridable values safely fall back to defaults:
- `EVIDENT_PATH`
- `EVOLUTION_DROP_PATH`
- `TRIOS_SCAN_ROOT`
- `SIGNATURE_DOCTORS_PATH` (project-local preferred, then legacy fallback)
- `TEMPLATE_DIR`
- `JOTFORM_PATH`
- `CC_IMPORTED_ROOT`

From `pyside6_ui.py`, UI preferences loaded from local settings safely fall back to defaults:
- `UI_THEME` -> `Default`
- `UI_LOGO` -> `ADS`
- `UI_COLOR_MODE` -> `color`
- `UI_DISPLAY_TITLE` -> app name
- `UI_DISPLAY_SUBTITLE` -> version text
- `UI_YEAR_OPTIONS` -> `2022..2027`
- `UI_DEFAULT_YEAR` -> `2026` (or first valid year)

## 3) Settings dialog behavior when file is absent

**Result: works.**

Why:
- Normal Settings fields are initialized from current in-memory config/UI defaults.
- Dialog does not require `local_settings.json` to exist before opening.

## 4) Save behavior when file is absent

**Result: creates file correctly.**

Why:
- `save_settings_updates(updates)`:
  - loads current settings (`{}` when missing),
  - merges updates,
  - writes JSON to temp path (`local_settings.json.tmp`),
  - atomically replaces into `local_settings.json` via `os.replace`.

This produces a valid JSON object file on first save.

## 5) Current risks / edge cases (first-run relevant)

- If the app directory is not writable for the current user, first save will fail (UI currently shows settings error dialog).
- If an existing `local_settings.json` is malformed, load falls back to `{}` (safe launch), and first successful save will overwrite malformed content with valid JSON.
- Restart is still required for path-level config changes to fully affect already-imported backend/config modules in the running process.

## 6) Is manually pre-creating `local_settings.json` required?

**No.**  
Manual pre-creation is not necessary for first-run operation.

- App launch works without it.
- Settings save creates it when needed.

## 7) Packaging-facing robustness improvement needed?

No additional code change is required for missing-file robustness at this time.

Current implementation already:
- launches safely when absent,
- uses conservative fallback defaults,
- creates `local_settings.json` on first save atomically.
