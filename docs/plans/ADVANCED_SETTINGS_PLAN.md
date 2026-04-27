# Advanced Settings Plan (Implemented Admin-Gated Dialog)

## Final editable advanced fields

Advanced Settings dialog now edits exactly:

- `EV_INT_BASE`
- `EVO_USER`
- `EVO_PASS`
- `IMG_USER`
- `IMG_PASS`

## Field masking in UI

Password-like fields are masked:

- `EVO_PASS` (masked)
- `IMG_PASS` (masked)

Other fields remain plain editable text.

## How values are loaded

- Dialog populates fields from current in-memory config values:
  - `EV_INT_BASE`, `EVO_USER`, `EVO_PASS`, `IMG_USER`, `IMG_PASS`
- These values already include current override resolution rules from `config.py`.

## How values are saved

- Save action writes through `admin_settings.save_admin_settings_updates(...)`.
- Save behavior:
  - merges updates into `admin_settings.json`,
  - preserves unrelated existing keys when file contains valid JSON object,
  - writes valid JSON using atomic replace (`.tmp` then `os.replace`).

## Behavior when `admin_settings.json` does not exist

- Save will create `admin_settings.json`.
- If file is missing/malformed/non-object during load, it is treated as empty (`{}`) safely.
- Runtime defaults/fallbacks remain in effect unless non-empty overrides are saved.

## Restart requirement

- Changes to advanced settings require app restart to fully apply to already-imported modules/config values.
- Save success message explicitly notes restart requirement.

## Admin gate behavior

- `Advanced Settings` button checks `current_user_is_admin()` first.
- If not admin, it shows exactly:
  - `Admin login required to access advanced settings`
- If admin, it opens the real Advanced Settings dialog.

## Tiny helper additions

- No new helper additions were required in `admin_settings.py` beyond the previously added conservative save helper:
  - `save_admin_settings_updates(updates)`.

## Risks / limitations

- Sensitive values are stored in plain JSON text (`admin_settings.json`) when used.
- This step intentionally does not add encryption/keychain integration.

## Safety confirmation

- No XML generation logic changed.
- No case processing logic changed.
- No template selection behavior changed.
- No scan naming/routing/output naming/substitution/ID generation logic changed.
