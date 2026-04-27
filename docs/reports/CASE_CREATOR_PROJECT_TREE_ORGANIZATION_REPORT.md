# CASE CREATOR PROJECT TREE ORGANIZATION REPORT

## 1. Summary of changes

This pass reorganized **loose top-level documentation, tooling, examples, legacy assets, and Windows scripts** into a clearer folder layout. **No intentional runtime behavior changes** were made to the live importer pipeline, business rules, template selection, routing, settings, or YAML business-rule loading.

Internal packages **`domain/`**, **`infrastructure/`**, and **`templates/`** were **not restructured**.

Primary runtime Python modules (**`pyside6_ui.py`**, **`case_processor_final_clean.py`**, **`import_service.py`**, **`config.py`**, etc.) **remain at the repository root** so imports, working-directory assumptions, and PyInstaller entrypoint paths stay stable.

## 2. New project tree overview

High-level layout (new or emphasized folders):

- **`docs/audits/`** — long-form audits and log/UI audits.
- **`docs/plans/`** — restructuring, blueprint, deployment, duplicate-retirement, migration, and feature plans.
- **`docs/reports/`** — Case Creator pass reports (rule centralization, live config, YAML migration, loader report).
- **`docs/packaging/`** — packaging and path audits, PyInstaller plans, hardening notes.
- **`docs/ui/`** — UI transition/replacement/layout plans and related UI planning docs.
- **`scripts/windows/`** — canonical Windows batch implementations (build, deploy, launchers).
- **`tools/`** — diagnostic / probe Python utilities (Evolution fetch/probe/test helpers).
- **`examples/`** — example JSON settings files for local/admin settings.
- **`legacy/`** — non-primary runtime and archival material:
  - **`legacy/import_gui.pyw`** — Tkinter UI implementation (invoked via root shim).
  - **`legacy/manual_import.py`** — legacy manual helper implementation (re-exported from root shim).
  - **`legacy/test_scripts/`** — former `Test scripts/` duplicate mirror (archival / non-authoritative).
  - **`legacy/reference/`** — large reference XML artifact moved out of the root.

**Root** now holds core runtime Python, **`business_rules/`**, **`requirements.txt`**, thin **launcher/build/deploy shims**, and this report.

## 3. Files moved

### Documentation

| Old path | New path |
|----------|----------|
| `CASE_CREATOR_FULL_AUDIT.md` | `docs/audits/CASE_CREATOR_FULL_AUDIT.md` |
| `UI_LOG_MESSAGE_AUDIT.md` | `docs/audits/UI_LOG_MESSAGE_AUDIT.md` |
| `CASE_CREATOR_RESTRUCTURE_PLAN.md` | `docs/plans/CASE_CREATOR_RESTRUCTURE_PLAN.md` |
| `CASE_CREATOR_RULE_CENTRALIZATION_BLUEPRINT.md` | `docs/plans/CASE_CREATOR_RULE_CENTRALIZATION_BLUEPRINT.md` |
| `CASE_CREATOR_CONFIG_EXPOSURE_PLAN.md` | `docs/plans/CASE_CREATOR_CONFIG_EXPOSURE_PLAN.md` |
| `WINSPARKLE_UPDATE_PLAN.md` | `docs/plans/WINSPARKLE_UPDATE_PLAN.md` |
| `DEPLOYMENT_PLAN_4_MACHINES.md` | `docs/plans/DEPLOYMENT_PLAN_4_MACHINES.md` |
| `DUPLICATE_TREE_ANALYSIS.md` | `docs/plans/DUPLICATE_TREE_ANALYSIS.md` |
| `DUPLICATE_RETIREMENT_PLAN.md` | `docs/plans/DUPLICATE_RETIREMENT_PLAN.md` |
| `ADMIN_ACCESS_PLAN.md` | `docs/plans/ADMIN_ACCESS_PLAN.md` |
| `IMPORT_SERVICE_PLAN.md` | `docs/plans/IMPORT_SERVICE_PLAN.md` |
| `ADVANCED_SETTINGS_PLAN.md` | `docs/plans/ADVANCED_SETTINGS_PLAN.md` |
| `LOCAL_SETTINGS_MIGRATION.md` | `docs/plans/LOCAL_SETTINGS_MIGRATION.md` |
| `LOCAL_SETTINGS_FIRST_RUN_CHECK.md` | `docs/plans/LOCAL_SETTINGS_FIRST_RUN_CHECK.md` |
| `CASE_CREATOR_FIRST_RULE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_FIRST_RULE_PASS_REPORT.md` |
| `CASE_CREATOR_SECOND_RULE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_SECOND_RULE_PASS_REPORT.md` |
| `CASE_CREATOR_THIRD_RULE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_THIRD_RULE_PASS_REPORT.md` |
| `CASE_CREATOR_FOURTH_RULE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_FOURTH_RULE_PASS_REPORT.md` |
| `CASE_CREATOR_FIFTH_RULE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_FIFTH_RULE_PASS_REPORT.md` |
| `CASE_CREATOR_SIXTH_RULE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_SIXTH_RULE_PASS_REPORT.md` |
| `CASE_CREATOR_SEVENTH_RULE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_SEVENTH_RULE_PASS_REPORT.md` |
| `CASE_CREATOR_CONFIG_LOADER_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_CONFIG_LOADER_PASS_REPORT.md` |
| `CASE_CREATOR_DOCTOR_OVERRIDE_LIVE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_DOCTOR_OVERRIDE_LIVE_PASS_REPORT.md` |
| `CASE_CREATOR_SHADE_OVERRIDE_LIVE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_SHADE_OVERRIDE_LIVE_PASS_REPORT.md` |
| `CASE_CREATOR_ROUTING_OVERRIDE_LIVE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_ROUTING_OVERRIDE_LIVE_PASS_REPORT.md` |
| `CASE_CREATOR_ARGEN_MODES_LIVE_PASS_REPORT.md` | `docs/reports/CASE_CREATOR_ARGEN_MODES_LIVE_PASS_REPORT.md` |
| `CASE_CREATOR_YAML_CONFIG_MIGRATION_REPORT.md` | `docs/reports/CASE_CREATOR_YAML_CONFIG_MIGRATION_REPORT.md` |
| `PYINSTALLER_BUILD_PLAN.md` | `docs/packaging/PYINSTALLER_BUILD_PLAN.md` |
| `PACKAGING_HARDENING_PLAN.md` | `docs/packaging/PACKAGING_HARDENING_PLAN.md` |
| `PACKAGED_PATH_AUDIT.md` | `docs/packaging/PACKAGED_PATH_AUDIT.md` |
| `PACKAGING_PREP_AUDIT.md` | `docs/packaging/PACKAGING_PREP_AUDIT.md` |
| `UI_REPLACEMENT_READINESS.md` | `docs/ui/UI_REPLACEMENT_READINESS.md` |
| `UI_TRANSITION_PLAN.md` | `docs/ui/UI_TRANSITION_PLAN.md` |
| `UI_LAYOUT_REFRESH_PLAN.md` | `docs/ui/UI_LAYOUT_REFRESH_PLAN.md` |
| `LOCAL_SETTINGS_UI_PLAN.md` | `docs/ui/LOCAL_SETTINGS_UI_PLAN.md` |
| `PYSIDE6_UI_PLAN.md` | `docs/ui/PYSIDE6_UI_PLAN.md` |

### Tooling / examples / legacy assets

| Old path | New path |
|----------|----------|
| `rx_fetch_and_parse.py` | `tools/rx_fetch_and_parse.py` |
| `evo_terminal_probe.py` | `tools/evo_terminal_probe.py` |
| `test_evo_request.py` | `tools/test_evo_request.py` |
| `local_settings.example.json` | `examples/local_settings.example.json` |
| `admin_settings.example.json` | `examples/admin_settings.example.json` |
| `dr prefs.xml` | `legacy/reference/dr prefs.xml` |
| `Test scripts/` (folder) | `legacy/test_scripts/` |

### Legacy Python (implementation moved; root compatibility preserved)

| Old path | New path |
|----------|----------|
| `import_gui.pyw` (full implementation) | `legacy/import_gui.pyw` (implementation + repo-root `sys.path` bootstrap) |
| `manual_import.py` (full implementation) | `legacy/manual_import.py` (implementation + repo-root `sys.path` bootstrap) |

### Windows batch scripts (implementation relocated; root shims added)

| Role | Root shim (unchanged name for habits/tooling) | Canonical implementation |
|------|-----------------------------------------------|-------------------------|
| PyInstaller build | `build_pyside6_onefolder.bat` | `scripts/windows/build_pyside6_onefolder.bat` |
| Primary launcher | `launch_importer.bat` | `scripts/windows/launch_importer.bat` |
| Tk fallback launcher | `launch_importer_tk_fallback.bat` | `scripts/windows/launch_importer_tk_fallback.bat` |
| Settings deploy helper | `deploy_casecreator_settings.bat` | `scripts/windows/deploy_casecreator_settings.bat` |

## 4. Files intentionally left in place

Kept at repository root (runtime-critical or packaging-sensitive):

- **`requirements.txt`** — standard dependency manifest location.
- **`pyside6_ui.py`** — primary PySide6 entrypoint (PyInstaller and daily launch).
- **`import_gui.pyw`** — **thin compatibility shim** forwarding to `legacy/import_gui.pyw`.
- **`case_processor_final_clean.py`**, **`import_service.py`**, **`template_utils.py`**, **`evo_to_case_data.py`**, **`evo_internal_client.py`**, **`evolution_case_detail.py`**
- **`config.py`**, **`local_settings.py`**, **`admin_settings.py`**, **`admin_access.py`**
- **`business_rules/`** — live editable rule store path is resolved relative to repo layout; left as-is.
- **`templates/`** — template bundle directory used by runtime and build scripts.
- **`domain/`**, **`infrastructure/`** — stable structured areas (untouched internally).
- Root **`.bat` shims** — preserve historical “double-click at repo root” workflows.

## 5. Compatibility measures

1. **`import_gui.pyw` (root)**  
   - Forwards execution to **`legacy/import_gui.pyw`** via `runpy.run_path`, preserving the historical root filename for launchers and shortcuts.

2. **`legacy/import_gui.pyw`**  
   - Prepends the repository root to `sys.path` so imports resolve the same modules as before when the UI file lives under `legacy/`.

3. **`manual_import.py` (root)**  
   - Re-exports symbols from **`legacy/manual_import.py`** via `importlib` so any external `from manual_import import ...` usage keeps working.

4. **`legacy/manual_import.py`**  
   - Prepends the repository root to `sys.path` for direct execution scenarios.

5. **`tools/*.py`**  
   - Adds the repository root to `sys.path` before importing `config` and other root modules.

6. **`legacy/test_scripts/*.py`**  
   - Appends the repository root to `sys.path` **after** the script directory, preserving the historical behavior where duplicate modules in that folder shadow root modules when executed from that folder.

7. **Windows launchers / build / deploy**  
   - Root `.bat` files are one-line `call` forwarders.  
   - Canonical scripts live in **`scripts/windows/`** and `pushd` to the repo root using `%~dp0..\..` (two levels up from `scripts/windows/`).  
   - **Launcher behavior change (intentional compatibility fix):** removed a previously hard-coded machine-specific `PROJECT_DIR` and replaced it with **repo-relative discovery** based on the batch file location. This avoids silently launching the wrong copy of the project when the repo is moved or cloned.

8. **`tools/rx_fetch_and_parse.py`**  
   - Fixed a **pre-existing tab/space indentation inconsistency** that prevented the file from being valid Python under modern parsers. This is **syntax-only**; control flow was not redesigned.

## 6. Validation performed

- **Import smoke test (core app):** `pyside6_ui`, `import_service`, `case_processor_final_clean`, and `infrastructure.config.business_rule_loader.load_business_rule_config_preview()` imported successfully.
- **`python -m compileall`** on `tools/`, `legacy/import_gui.pyw`, `legacy/manual_import.py`, root shims, and `legacy/test_scripts/` — passed after the `rx_fetch_and_parse.py` indentation fix.
- **Config path logic:** `business_rules/` and `infrastructure/config` were not moved; **no live YAML/JSON rule loading paths were changed** by this pass.
- **PyInstaller script expectations:** `build_pyside6_onefolder.bat` still `pushd`s to repo root and references `pyside6_ui.py`, `templates/`, and `case_creator_icon.ico` from that root.

**Not fully verified in this environment (stated limitation):**

- Windows-only double-click execution of `.bat` files (macOS workspace).
- End-to-end PyInstaller build output (not executed here).

## 7. Risks or limitations

- **Bookmarked documentation paths** may still point to old root locations; update links in wikis/chat archives as needed.
- **`manual_import` remains known-stale** relative to current processor exports (pre-existing); the new shim does not “fix” that incompatibility.
- **Direct references** to moved example JSON paths (e.g. docs mentioning `local_settings.example.json` at repo root) should be updated to `examples/`.
- **`dr prefs.xml`** moved to `legacy/reference/`; if any external non-repo process expected it at root, update that process.

## 8. Recommended next pass

The safest follow-up is **documentation hygiene only**:

- Add a short `docs/README.md` index linking to `audits/`, `plans/`, `reports/`, `packaging/`, and `ui/` (optional).
- Sweep internal markdown links for broken relative paths after the move.
- Optionally announce a deprecation window for root-vs-`scripts/windows/` batch duplication once team habits are migrated.

Avoid combining that with business-rule or processor refactors in the same pass.
