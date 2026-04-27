# UI Replacement Readiness Audit

This compares:
- Old UI: `import_gui.pyw` (Tkinter)
- New UI: `pyside6_ui.py` (PySide6)

Scope is UI behavior only. Frozen backend processing logic is not changed.

Current launcher default status:
- Primary/default launcher: `launch_importer.bat` -> `pyside6_ui.py`
- Legacy fallback launcher: `launch_importer_tk_fallback.bat` -> `import_gui.pyw`

## 1) Old UI user-visible features (`import_gui.pyw`)

- Main import window with year dropdown + case number input + import button.
- Enter key triggers import (`<Return>` bound at root).
- Queue behavior for multiple imports:
  - cases are queued (`self.queue`),
  - logs show queued message,
  - worker loop processes one by one.
- Rich colored log view with tags (`success`, `error`, `warn`, `template`, `route`, etc.).
- Status panel:
  - rainbow "online" indicator,
  - ngrok URL display auto-polled every 15 seconds.
- Import timeout note:
  - import thread joined with `timeout=60`,
  - logs timeout warning if thread still alive.
- Close protection:
  - blocks app close while import active/queue not empty.
- Local Flask endpoint:
  - `POST /import-case` for external automation-style triggering.

## 2) New UI user-visible features (`pyside6_ui.py`)

- Main import window with year dropdown + case number input + derived case ID preview + import button.
- Enter in case number input triggers import.
- Split read-only logs:
  - left `Case Summary`,
  - right `Process Log`,
  - exact routing rules implemented (see section 9).
- Import executed on background `QThread` worker; UI stays responsive.
- FIFO queue behavior for multiple import requests (queued and processed in order).
- Close protection while import active or queue non-empty.
- 60-second timeout warning (log warning only; no forced termination).
- Case-number field clears after import request is queued.
- Normal Settings dialog (implemented):
  - edits only `EVIDENT_PATH`, `TRIOS_SCAN_ROOT`, `CC_IMPORTED_ROOT`,
  - folder browse buttons,
  - save to `local_settings.json` (merge, preserve unrelated keys),
  - restart notice after save.
- Advanced Settings dialog (implemented):
  - admin-gated by `current_user_is_admin()`,
  - exact non-admin message: `Admin login required to access advanced settings`,
  - edits `EV_INT_BASE`, `EVO_USER`, `EVO_PASS`, `IMG_USER`, `IMG_PASS`,
  - password masking for `EVO_PASS` and `IMG_PASS`,
  - save to `admin_settings.json` (merge, preserve unrelated keys),
  - restart notice after save.
- App name/version display via `import_service.get_app_info()`.
- Uses `import_service.py` boundary (does not call frozen backend module directly).

## 3) Gaps: old UI still does things new UI does not

Priority order (highest operational impact first):

1. **No external Flask `/import-case` trigger in PySide6 runtime**
   - Tk UI starts a background Flask server for non-UI triggers.
   - PySide6 intentionally does not include this (deprecated by decision).

2. **No ngrok/online status panel**
   - Tk has top-right status + ngrok URL polling; PySide6 currently does not.

3. **Log presentation differs from Tk styling**
   - PySide6 now has color mode and dual-panel routing, but not identical Tk tag style/visual treatment.

## 4) New UI improvements/safety gains

- Cleaner separation from frozen backend via `import_service.py`.
- Built-in admin-gated Advanced Settings workflow (not present as functional UI in Tk).
- Normal and Advanced settings persistence layers are explicit, isolated, and merge-safe.
- Password masking in Advanced Settings.
- Settings save operations explicitly warn users restart is required.

## 5) Replacement readiness assessment

**Status: Not fully ready for production replacement yet.**

For normal manual operator workflow, PySide6 is functionally close.
Remaining non-deprecated gaps are mostly status-panel and presentation differences.

## 6) Smallest remaining gaps before safe replacement

Recommended minimal parity tasks (UI/shell only, no backend changes):

1. Decide if a status strip (online/ngrok-like indicator) is still operationally needed; if yes, add UI-only equivalent.
2. Finalize dual-log visual polish (line spacing, section emphasis, optional badges) without changing routing.
3. Confirm operator acceptance of Flask/ngrok deprecation in production rollout checklist.

## 7) Tiny low-risk UI-only improvements (not implemented in this audit)

- Clear case-number input after import start for parity.
- Add import start/finish emojis/text style for closer operator familiarity.
- Add read-only derived case ID copy affordance (optional).

No backend behavior changes are required for these parity improvements.

## 8) Follow-up Implementation Status (Current Pass)

This follow-up pass intentionally keeps all changes in the PySide6 shell/settings layer only.

### Intentionally deprecated (not rebuilt)

- Flask `/import-case` endpoint parity: **deprecated by decision**, not rebuilt.
- Ngrok status indicator/polling parity: **deprecated by decision**, not rebuilt.

Reason:
- These are no longer part of the active workflow.
- Avoids reintroducing unused background/network shell behavior.

### Parity gaps addressed in this pass

- FIFO queue behavior implemented in PySide6:
  - requests are queued and processed one-by-one in order.
- Close-while-busy guard implemented:
  - app close is blocked while import is active or queue has pending items.
- 60-second timeout warning parity implemented:
  - warning is logged only; running work is not killed.
- Input polish:
  - case-number field is cleared after request is accepted/queued.

### UI-only polish/settings additions in this pass

- Added Color/Standard mode toggle.
- Added theme support in Normal Settings (Default + creative options including Bubble Gum).
- Added configurable display title/subtitle in Normal Settings.
- Added editable year options/default-year controls in Normal Settings.

### Why this remains low-risk

- No XML or processing backend logic changed.
- No template-selection or output-path generation logic changed.
- Queue/guard/timeout work is implemented in UI orchestration only.
- All settings changes are persisted through existing settings JSON helpers with merge-safe writes.

## 9) Final Dual-Log Routing (Current State)

### Left panel (`Case Summary`) exact routes

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

### Right panel (`Process Log`) exact routes

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

Implementation safeguard:
- Any unexpected/unlisted message is routed to `Process Log` by default so no message is dropped.
