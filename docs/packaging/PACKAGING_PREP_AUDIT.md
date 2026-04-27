# Packaging Prep Audit (PySide6 -> PyInstaller)

This is a conservative pre-packaging audit only. No packaging execution is performed here.

## 1) Canonical Packaging Entrypoint

- **Primary app entrypoint for packaging:** `pyside6_ui.py`
- Current source launcher default (`launch_importer.bat`) already points to `pyside6_ui.py`.
- Tkinter fallback (`import_gui.pyw`) is retained but should not be the packaged default entry.

## 2) Runtime-Required Files/Folders to Include

## A) Required code modules (bundled)

- `pyside6_ui.py`
- `import_service.py`
- `admin_access.py`
- `local_settings.py`
- `admin_settings.py`
- `config.py`
- `case_processor_final_clean.py`
- `template_utils.py`
- `evo_internal_client.py`
- `evo_to_case_data.py`
- `evolution_case_detail.py`
- plus transitive imports used by above.

## B) Required bundled data/assets

- `templates/` (entire folder)
  - observed footprint: 16 template subfolders, 52 files total.
  - includes per-template XML + `Materials.xml` + `Manufacturers.3ml`.
- `List of Signature Dr.xlsx`
  - required by `template_utils.is_signature_doctor()` via `pandas.read_excel(..., engine="openpyxl")`.

## C) Optional/non-critical project files (not required for core app runtime)

- `launch_importer*.bat` (source launch convenience, not required once packaged executable exists)
- docs (`*.md`)
- test/probe scripts (`rx_fetch_and_parse.py`, `evo_terminal_probe.py`, `test_evo_request.py`) unless intentionally packaged as tools.
- `dr prefs.xml`, `case_creator_icon.ico`, installer exe artifact (only include if specifically needed by packaging plan).

## 3) Asset vs Local Settings vs External Dependencies

## Bundled app assets (ship inside package)

- Code modules above.
- `templates/`.
- `List of Signature Dr.xlsx`.

## User/machine-local settings (should stay external and writable)

- `local_settings.json` (optional; created on first settings save)
- `admin_settings.json` (optional; created on first advanced settings save)

## External runtime dependencies (not bundled content)

- Network/mapped path roots configured by settings/config:
  - `EVIDENT_PATH`
  - `TRIOS_SCAN_ROOT`
  - `CC_IMPORTED_ROOT`
  - optional/legacy: `JOTFORM_PATH`, `EVOLUTION_DROP_PATH`
- EVO/internal services:
  - `EV_INT_BASE`
  - credentials and image server credentials (from env/admin settings/config fallback)

## 4) Current Path Logic / Assumptions to Watch

## Script-directory-relative logic (good for packaging if used carefully)

- `local_settings.py` and `admin_settings.py` resolve JSON paths via `os.path.dirname(os.path.abspath(__file__))`.
- `config.py` resolves signature-doctor default from project/app directory first:
  - `<app_dir>/List of Signature Dr.xlsx` (fallback to legacy absolute path).

## Absolute-path default still present (packaging risk)

- `config.py` default for `TEMPLATE_DIR` is still legacy absolute user path:
  - `C:\Users\kkollarova\Documents\3shape_case_importer\templates`
- In packaged deployment this should usually come from local settings (or a packaging-safe default strategy).

## CWD assumptions

- Core runtime file lookup relies mostly on configured paths and script-directory resolution, not current working directory.
- Existing `.bat` launchers do `pushd`, but packaged `.exe` launch typically should not rely on that.

## 5) PyInstaller Risk Notes

## High-likelihood packaging risks

1. **One-file mode vs settings persistence**
   - With one-file, `__file__`-based paths may point into temporary extraction directories.
   - `local_settings.json` / `admin_settings.json` persistence and writable location become fragile.
   - **Recommendation:** prefer **one-folder** build first.

2. **Template asset inclusion**
   - Missing `templates/` at runtime will break template selection/output generation.

3. **Excel asset + engine dependency**
   - Missing `List of Signature Dr.xlsx` or `openpyxl` runtime can break signature-doctor logic.

4. **PySide6 plugin/resource handling**
   - Qt platform/plugins usually require proper collection by PyInstaller.

5. **Over-broad dependency set**
   - `requirements.txt` includes many unrelated heavy packages; packaging all may increase size/risk.
   - Consider a minimal packaging environment later (planning item, no change now).

## Potential hidden-import/data concerns

- `pandas` + `openpyxl` chain.
- PySide6 Qt plugins.
- `requests`/TLS cert handling in packaged environment (verify EVO HTTPS behavior).

## 6) One-Folder vs One-File Recommendation

**Safer initial choice: one-folder build.**

Why:
- Better transparency for bundled assets (`templates/`, Excel file).
- Easier debugging of missing resources.
- More predictable writable location strategy for external JSON settings.
- Lower risk than one-file extraction path behavior for this app’s current settings-path approach.

## 7) Expected Settings Behavior in Packaged Deployment

- If `local_settings.json`/`admin_settings.json` are absent:
  - app should still launch using defaults.
- Saving from settings should create these files.
- For robust packaging behavior, ensure these JSON files live in a stable writable location (not transient extraction path).
- Restart requirements remain:
  - path/config changes require restart for full effect in already-loaded modules.

## 8) Launcher/Shortcut Guidance After Packaging

- Packaged deployment should point desktop/start-menu shortcut directly to packaged PySide6 executable.
- Source `.bat` launchers become development/fallback artifacts, not primary packaged launch path.
- Keep Tkinter fallback in source during transition; packaged default remains PySide6.

## 9) First Packaged Smoke Test Checklist

## Boot and settings

- Launch packaged app with no preexisting `local_settings.json`.
- Open Normal Settings and save path values.
- Confirm `local_settings.json` is created and persists.
- Open Advanced Settings (admin) and save; confirm `admin_settings.json` creation/persistence.

## Import flow

- Run single-case import end-to-end.
- Verify both log panels receive expected message classes.
- Verify queue behavior with 2+ imports.
- Verify close guard while import/queue active.
- Verify 60-second warning behavior remains log-only.

## Output integrity spot-check

- Confirm output folder placement and naming match expected behavior.
- Confirm XML file is generated and includes expected structure (no behavior drift).
- Confirm required support files copied (`Materials.xml`, `Manufacturers.3ml`, scans/pdf where applicable).

## Asset/path checks

- Verify template resolution uses packaged/expected template path strategy.
- Verify signature-doctor Excel is readable in packaged runtime.
- Verify external mapped/network paths still accessible from packaged process context.

## 10) Obvious Packaging Blockers (Documented, Not Refactored)

1. `TEMPLATE_DIR` legacy absolute default is not packaging-friendly unless overridden by settings.
2. Settings JSON path strategy uses `__file__`; one-file build can make persistence path behavior undesirable.
3. Packaging from full current requirements list may pull many unnecessary heavy deps and increase failure surface.

No code refactor applied in this step; these are planning blockers to address deliberately in packaging implementation phase.
