# Local Settings UI Plan (Implemented + Parity/Polish Pass)

## Final implemented Normal Settings fields

Normal Settings currently exposes:

### Path fields (machine-specific)
- `EVIDENT_PATH`
- `TRIOS_SCAN_ROOT`
- `CC_IMPORTED_ROOT`

Each path field includes:
- clear label,
- editable text input,
- `Browse` button,
- folder picker (`QFileDialog.getExistingDirectory`).

### UI preference fields
- `UI_THEME` (theme selector)
- `UI_LOGO` (logo selector)
- `UI_DISPLAY_TITLE` (editable title)
- `UI_DISPLAY_SUBTITLE` (editable subtitle)
- `UI_YEAR_OPTIONS` (editable year list: add/remove)
- `UI_DEFAULT_YEAR` (default-year selector)

## Hidden/not shown in Normal Settings

These remain in runtime config but are intentionally hidden from Normal Settings UI:
- `JOTFORM_PATH`
- `EVOLUTION_DROP_PATH`
- `SIGNATURE_DOCTORS_PATH`
- `TEMPLATE_DIR`

## Theme selection behavior

- Theme list includes:
  - `Default` (first option),
  - plus 10 creative themes (including `Bubble Gum`).
- Color application is controlled by the main-window Color/Standard toggle:
  - `Standard` => plain/simple Qt presentation,
  - `Color` => selected theme palette applied.
- Theme selection is saved in local settings and applied immediately to current UI shell after save.

## Logo selection behavior

- Logo selector is a Normal Settings dropdown (`UI_LOGO`).
- Default option is `ADS`.
- Final logo option set:
  - `ADS`
  - `Crown Club`
  - `Smile`
  - `♡ Sugar Baby ♡`
  - `Smiley`
  - `Sunglasses`
  - `Star Cats`
  - `(╥﹏╥)`
  - `Coffee`
  - `Shrug`
- Selected logo is saved and reloaded on restart.
- Selected logo is also applied immediately after Settings save.
- Multi-line text-art logos are supported in the centered logo area:
  - single-line logos use the normal larger display size,
  - multi-line logos use roughly half-size for fit/readability.

## Title/subtitle behavior

- `UI_DISPLAY_TITLE` and `UI_DISPLAY_SUBTITLE` control user-facing top text in the PySide6 window.
- They replace the old hardcoded single display line behavior in the new shell.
- Changes apply immediately after Save in current UI session.
- Backend behavior is unaffected.

## Editable year list/default-year behavior

- Users can:
  - view available years,
  - add a year,
  - remove selected year,
  - choose default year.
- Conservative validation:
  - year must be 4-digit numeric string.
- Conservative fallback:
  - if configuration becomes invalid/empty, UI falls back to built-in defaults (`2022..2027`, default `2026`).
- Saved values apply immediately to the current year dropdown in the current UI session.

## How values are loaded

- Path fields are loaded from current in-memory `config.py` values.
- UI preference fields are loaded from `local_settings.json` (with conservative fallback defaults if missing/invalid).

## How values are saved

- Save action writes to `local_settings.json` through:
  - `local_settings.save_settings_updates(updates)`.
- Save behavior:
  - merges updates into existing JSON object,
  - preserves unrelated keys when existing JSON is valid,
  - writes valid JSON via atomic replace (`.tmp` then `os.replace`),
  - does not delete hidden/internal keys.
- Normal Settings save is silent on success (no success popup).

## Behavior when `local_settings.json` does not exist

- Save creates `local_settings.json` automatically.
- Missing/malformed file is treated safely as empty settings.

## Restart requirements vs immediate apply

- **Requires restart for full effect:**
  - `EVIDENT_PATH`
  - `TRIOS_SCAN_ROOT`
  - `CC_IMPORTED_ROOT`
  (because backend/config modules are already loaded in-process)

- **Applied immediately in current PySide6 shell:**
  - `UI_THEME` (in color mode)
  - `UI_COLOR_MODE`
  - `UI_LOGO`
  - `UI_DISPLAY_TITLE`
  - `UI_DISPLAY_SUBTITLE`
  - `UI_YEAR_OPTIONS`
  - `UI_DEFAULT_YEAR`

## Readability overrides (implemented)

Regardless of theme/mode:
- `Case Summary` pane background stays white.
- `Process Log` pane background stays white.
- year selector background stays white.
- case-number input background stays white.
- text color for these controls is forced to dark/readable.

## Case Summary block formatting (implemented)

Each case summary block:
- starts with a case-id-only line,
- ends with `--------------------------------------------`.

## Notes on `SIGNATURE_DOCTORS_PATH` portability

Already implemented conservatively in `config.py`:
- default resolves project-local `List of Signature Dr.xlsx` first,
- legacy absolute fallback retained,
- optional local settings override still supported.

## Safety confirmation

- No XML generation logic changed.
- No case processing logic changed.
- No template selection logic changed.
- No scan naming/routing/output naming/substitution/ID generation changed.
- Normal Settings changes are UI/settings-layer only.

