# UI Log Message Audit (PySide6 Import Flow)

This audit inventories user-visible log/messages in the current PySide6 import flow.

## Scope and Message Path

- UI entrypoint: `pyside6_ui.py`
- UI-facing backend boundary: `import_service.import_case_by_id()`
- Backend callback source: `case_processor_final_clean.process_case_from_id()` and `process_case()`

Indirect callback path:
1. backend emits `log_callback(...)` strings
2. `ImportWorker.emit_log()` forwards to Qt signal
3. `MainWindow._append_log()` writes to log widget

So many log lines are backend-originated but UI-rendered.

---

## 1) Inventory by Source

## A. `pyside6_ui.py` (direct UI-originated messages)

| Message (exact or template) | Source | Type |
|---|---|---|
| `Ready for case ID input.` | `MainWindow._setup_ui()` -> `_append_log` | process/procedural |
| `Queued case: {case_id}` | `MainWindow._start_import()` | process/procedural |
| `--------------------------------------------` | `MainWindow._start_next_import()` | process/procedural |
| `Starting import: {case_id}` | `MainWindow._start_next_import()` | process/procedural |
| `Queue empty.` | `MainWindow._start_next_import()` and `_clear_thread_refs()` | completion/result |
| `⚠️ Timeout warning: Case {case_id} has been running over 60 seconds.` | `MainWindow._warn_if_still_running()` | warning/error |
| `Error while importing: {error_message}` | `MainWindow._on_import_error()` | warning/error |
| `Finished: {finished_case}` | `MainWindow._on_import_finished()` | completion/result |

Import-flow related message dialogs (not log area):

| Message | Source | Type |
|---|---|---|
| `Please enter a valid case ID.` | `QMessageBox.warning` in `_start_import()` | warning/error |
| `Cannot close program while import is in progress or queue is not empty.` | `QMessageBox.warning` in `closeEvent()` | warning/error |

Note: `Settings` and `Advanced Settings` save/error dialogs exist, but they are outside core import flow logging.

## B. `case_processor_final_clean.py` (backend callback messages rendered in UI log)

These are emitted via `log_callback(...)` and appear in the PySide6 log area.

| Message (exact/template) | Source function | Type |
|---|---|---|
| `⚠️ Could not remove existing zip: {e}` | `zip_case_folder()` | warning/error |
| `📦 Created zip: {zip_path}` | `zip_case_folder()` | completion/result |
| `❌ Multiple units — manual import required` | `process_case()` | warning/error |
| `🦷 Detected teeth: {', '.join(sorted(teeth))}` | `process_case()` | case-summary style |
| `🦷 EVO reports units > 1` | `process_case()` | case-summary style |
| `❌ Manual import required — material: {material_hint}` | `process_case()` | warning/error |
| `❌ Manual import required — unsupported material (not Envision/Adzir)` | `process_case()` | warning/error |
| `🧱 MODELESS CASE (Argen)` | `process_case()` | case-summary style |
| `📦 Starting import: {case_id}` | `process_case()` | process/procedural |
| `Pt: {first} {last}, Dr. {doctor}` | `process_case()` | case-summary style |
| `🦷 Tooth = {tooth_or_unknown}` | `process_case()` | case-summary style |
| `👤 SIGNATURE DR` | `process_case()` | case-summary style |
| `🖋 HAS A STUDY` | `process_case()` (3Shape study check path) | case-summary style |
| `❌ NO STUDY AVAILABLE` | `process_case()` (multiple branches) | warning/error |
| `🧪 HAS A STUDY` | `process_case()` (rename_scans path) | case-summary style |
| `🟡 JOTFORM CASE, requires manual import` | `process_case()` | warning/error |
| `ANTERIOR` | `process_case()` | case-summary style |
| `📄 Using template: {os.path.basename(template_path)}` | `process_case()` | process/procedural |
| `🏭 ARGEN CASE` | `process_case()` | case-summary style |
| `🧑‍🎓 DESIGNER CASE` | `process_case()` | case-summary style |
| `🧑‍🎓 SERBIA CASE` | `process_case()` | case-summary style |
| `🤖 DESIGNER CASE` | `process_case()` | case-summary style |
| `🤖 SERBIA CASE` | `process_case()` | case-summary style |
| `🧹 Removed unzipped folder: {final_output}` | `process_case()` | process/procedural |
| `⚠️ Failed to remove unzipped folder: {e}` | `process_case()` | warning/error |
| `Itero Case` | `process_case_from_id()` | case-summary style |
| `Itero Case (fallback)` | `process_case_from_id()` | case-summary style |
| `📁 Found matching folder in {portal}/{date_folder}` | `process_case_from_id()` | process/procedural |
| `📁 (fallback) Found matching folder in {portal}/{date_folder}` | `process_case_from_id()` | process/procedural |

## C. `case_processor_final_clean.py` return messages surfaced by worker

`ImportWorker.run()` logs return value from `import_case_by_id(...)` when non-`None`:

| Message template | Origin | Type |
|---|---|---|
| `Completed {case_id} → {zip_path}` | `process_case()` return | completion/result |
| `Completed {case_id} → {final_output}` | `process_case()` return | completion/result |
| `❌ Manual import required — material` | `process_case()` return | warning/error |
| `🟡 JOTFORM CASE, requires manual import` | `process_case()` return (same string as callback in that branch) | warning/error |

## D. Exception-derived messages surfaced by UI

Any raised exception not handled into callback text appears as:

| Template | Source | Type |
|---|---|---|
| `Error while importing: {error_message}` | `MainWindow._on_import_error()` | warning/error |

`{error_message}` can be dynamic text from backend exceptions, e.g. file-not-found/value errors.

---

## 2) Inventory by Message Type

## Case-summary style

- `Pt: {first} {last}, Dr. {doctor}`
- `🦷 Tooth = {tooth_or_unknown}`
- `👤 SIGNATURE DR`
- `🖋 HAS A STUDY`
- `🧪 HAS A STUDY`
- `ANTERIOR`
- `🏭 ARGEN CASE`
- `🧑‍🎓 DESIGNER CASE`
- `🧑‍🎓 SERBIA CASE`
- `🤖 DESIGNER CASE`
- `🤖 SERBIA CASE`
- `🧱 MODELESS CASE (Argen)`
- `Itero Case`
- `Itero Case (fallback)`
- `🦷 Detected teeth: ...`
- `🦷 EVO reports units > 1`

## Process/procedural

- `Ready for case ID input.`
- `Queued case: {case_id}`
- `--------------------------------------------`
- `Starting import: {case_id}`
- `📦 Starting import: {case_id}`
- `📄 Using template: {template_filename}`
- `📁 Found matching folder in ...`
- `📁 (fallback) Found matching folder in ...`
- `🧹 Removed unzipped folder: {final_output}`

## Warning/error

- `Please enter a valid case ID.` (dialog)
- `Cannot close program while import is in progress or queue is not empty.` (dialog)
- `⚠️ Timeout warning: Case ...`
- `Error while importing: {error_message}`
- `❌ NO STUDY AVAILABLE`
- `⚠️ Could not remove existing zip: ...`
- `⚠️ Failed to remove unzipped folder: ...`
- `❌ Multiple units — manual import required`
- `❌ Manual import required — material: ...`
- `❌ Manual import required — unsupported material (not Envision/Adzir)`
- `❌ Manual import required — material`
- `🟡 JOTFORM CASE, requires manual import`

## Completion/result

- `Finished: {finished_case}`
- `Queue empty.`
- `📦 Created zip: {zip_path}`
- `Completed {case_id} → {zip_path}`
- `Completed {case_id} → {final_output}`

---

## 3) Proposed First-Pass Split Classification

## Recommended for left “Case Summary” panel

- `Pt: ...`
- `🦷 Tooth = ...`
- `👤 SIGNATURE DR`
- `ANTERIOR`
- `... HAS A STUDY` / `NO STUDY AVAILABLE` (high-level state)
- Route/family tags (`🏭 ARGEN CASE`, `🧑‍🎓 ...`, `🤖 ...`, `🧱 MODELESS CASE`)
- Manual-import reason summaries (`❌ ... manual import ...`, `🟡 JOTFORM ...`)
- Multi-unit summary (`❌ Multiple units ...`, detected teeth/units detail)

## Recommended for right “Process Log” panel

- Queue lifecycle (`Queued case`, `Starting import`, separator, `Finished`, `Queue empty`)
- Folder/template/procedural steps (`📁 Found matching folder...`, `📄 Using template...`, zip/remove logs)
- Timeout warnings and raw exception lines (`⚠️ Timeout warning...`, `Error while importing: ...`)
- Completion paths (`Completed ... → ...`, `📦 Created zip: ...`)

## Ambiguous / needs human decision

- `❌ NO STUDY AVAILABLE` (can be summary status or procedural warning)
- `⚠️ Could not remove existing zip ...` / `⚠️ Failed to remove unzipped folder ...` (operational warning vs backend housekeeping detail)
- `Ready for case ID input.` (status banner vs process log preface)

