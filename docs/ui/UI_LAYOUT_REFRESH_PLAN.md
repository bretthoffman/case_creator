# UI Layout Refresh Plan (PySide6, UI-Only)

## Top Layout Proposal (Implemented in this pass)

- Left side:
  - `Import Case` button remains on the left side of the top action row.
- Center:
  - semi-transparent, decorative logo label (no border/panel).
  - logo text comes from Normal Settings `Logo` selection.
- Right side:
  - compact vertical stack:
    - `Settings`
    - `Advanced Settings`
    - `Color/Standard` toggle

This keeps import action visually primary while moving settings controls to a compact utility column.

## Lower Layout Proposal (Implemented in this pass)

Lower area is split into two sections:

- Left: `Case Summary`
- Right: `Process Log`

Both are read-only log panes and remain fed by the same existing message stream.

## Two-Panel Log Routing

Routing strategy is UI-only and non-destructive:

- `Case Summary` (left) receives exactly:
  - `Pt: {first} {last}, Dr. {doctor}`
  - `🦷 Tooth = {tooth_or_unknown}`
  - `👤 SIGNATURE DR`
  - `🖋 HAS A STUDY`
  - `🧪 HAS A STUDY`
  - `❌ NO STUDY AVAILABLE`
  - `ANTERIOR`
  - `🧱 MODELESS CASE (Argen)`
  - `🏭 ARGEN CASE`
  - `🧑‍🎓 DESIGNER CASE`
  - `🧑‍🎓 SERBIA CASE`
  - `🤖 DESIGNER CASE`
  - `🤖 SERBIA CASE`
  - `Itero Case`
  - `Itero Case (fallback)`
  - `🦷 Detected teeth: {', '.join(sorted(teeth))}`
  - `🦷 EVO reports units > 1`
  - `❌ Multiple units — manual import required`
  - `❌ Manual import required — material: {material_hint}`
  - `❌ Manual import required — unsupported material (not Envision/Adzir)`
  - `❌ Manual import required — material`
  - `🟡 JOTFORM CASE, requires manual import`

- `Process Log` (right) receives exactly:
  - `Ready for case ID input.`
  - `Queued case: {case_id}`
  - `--------------------------------------------`
  - `Starting import: {case_id}`
  - `📦 Starting import: {case_id}`
  - `📁 Found matching folder in {portal}/{date_folder}`
  - `📁 (fallback) Found matching folder in {portal}/{date_folder}`
  - `📄 Using template: {os.path.basename(template_path)}`
  - `📦 Created zip: {zip_path}`
  - `🧹 Removed unzipped folder: {final_output}`
  - `⚠️ Could not remove existing zip: {e}`
  - `⚠️ Failed to remove unzipped folder: {e}`
  - `⚠️ Timeout warning: Case {case_id} has been running over 60 seconds.`
  - `Error while importing: {error_message}`
  - `Finished: {finished_case}`
  - `Queue empty.`
  - `Completed {case_id} → {zip_path}`
  - `Completed {case_id} → {final_output}`

Any unexpected/unlisted message is routed to `Process Log` by default so no message is silently dropped.

## Case Summary Block Separation (Implemented)

For each imported case in `Case Summary`:

- block starts with a line containing only the case ID (example: `2026-15582`),
- block ends with:
  - `--------------------------------------------`

Existing summary-class messages are preserved inside each block.

## Logo Behavior and Persistence

- New Normal Settings option: `Logo` dropdown.
- Default option: `ADS`.
- Revised logo set:
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
- Selected logo is saved to `local_settings.json` under `UI_LOGO`.
- Selected logo is applied immediately in the live PySide6 UI after Settings save.
- On restart, logo is reloaded from settings.
- Multi-line text-art logos are supported in the centered display.
  - single-line logos render at the standard larger size,
  - multi-line logos render at roughly half-size so they fit comfortably.
- Logo remains centered and semi-transparent with no panel/border.

## Readability Decisions (Implemented)

To guarantee readability across themes/modes:

- `Case Summary` pane background is always white.
- `Process Log` pane background is always white.
- year selector background is always white.
- case-number input background is always white.
- text color for those white-background controls is forced to dark/readable.

## Color/Standard Button Label Behavior (Implemented)

- Button now shows the **current** mode label:
  - `Color` when color mode is active,
  - `Standard` when standard mode is active.

## Why this remains low-risk

- Changes are limited to `pyside6_ui.py` and local UI settings persistence.
- No XML/backend processing paths were modified.
- No routing/template/scan/ID logic changed.
- Existing log messages remain intact; only UI presentation/routing changed.

