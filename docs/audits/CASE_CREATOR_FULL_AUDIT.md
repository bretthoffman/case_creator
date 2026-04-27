# CASE CREATOR FULL AUDIT

## 1. Executive Summary

Case Creator is a Windows-focused desktop importer that takes a case ID, pulls case details from an Evolution API, locates matching scan/source folders, applies a dense rule set to choose a 3Shape XML template and destination path, generates a final case package, and outputs it into destination queues (`Send to Argen`, `Send to 1.9`, or failure/manual paths).

Current architecture is functional but layered unevenly:
- **UI layer** exists in two parallel frontends (`pyside6_ui.py` primary, `import_gui.pyw` legacy Tk fallback).
- **Service layer** is minimal (`import_service.py`) and mostly pass-through.
- **Business logic** is concentrated in `case_processor_final_clean.py` and `template_utils.py`, with additional routing hints in `evo_to_case_data.py`.
- **Infrastructure/config** is split between `config.py`, `local_settings.py`, and `admin_settings.py`.
- **Template assets** are large static XML trees in `templates/`.

Biggest strengths:
- End-to-end flow is explicit and mostly synchronous/traceable.
- Templates and materials are file-based and already separated from Python logic.
- Local/admin settings persistence exists and supports packaged mode (`%LOCALAPPDATA%\CaseCreator` when frozen on Windows).

Biggest weaknesses:
- Business rules are spread across multiple modules and partially duplicated.
- Critical decisions depend on string matching and filename heuristics.
- Legacy and test/probe scripts coexist in runtime tree, creating ambiguity.
- Some code paths appear stale or inconsistent with current signatures.

Biggest risks for future edits:
- Unintended routing/template regressions due to intertwined conditions.
- Breaking scanner folder discovery logic (3Shape/iTero special handling).
- Packaging-time path/resource failures if config defaults are not preserved.
- Accidental behavior changes when “cleaning up” UI and service boundaries.

Biggest opportunities:
- Centralize rules into a single domain layer without changing behavior.
- Convert long conditional chains into explicit rule tables (still code-first initially).
- Separate scanner intake, template decision, and output routing into discrete modules.
- Treat config, secrets, and deployment defaults as first-class subsystems.

---

## 2. Project Tree Overview

### Core runtime source
- `pyside6_ui.py` - primary PySide6 desktop UI (queue, logs, settings dialogs, worker threading).
- `import_gui.pyw` - legacy Tkinter fallback UI + Flask `/import-case` endpoint.
- `import_service.py` - thin adapter for case ID validation/build and backend call.
- `case_processor_final_clean.py` - main processing pipeline (folder lookup, scan normalization, template/output routing, XML generation, packaging).
- `template_utils.py` - template selection and business-rule helper predicates.
- `evo_internal_client.py` - Evolution API client (`wsb_get_casedetail`).
- `evo_to_case_data.py` - converts parsed Evolution response into normalized `case_data` with route/material/shade hints.
- `evolution_case_detail.py` - XML response parser into structured dict.
- `config.py` - resolved runtime constants from settings + defaults.
- `local_settings.py` - local/user-editable settings persistence.
- `admin_settings.py` - admin/credential settings persistence.
- `admin_access.py` - Windows admin-rights check.

### Operational scripts
- `launch_importer.bat` - primary launcher (PySide6).
- `launch_importer_tk_fallback.bat` - legacy Tk fallback launcher.
- `build_pyside6_onefolder.bat` - PyInstaller one-folder build script.
- `deploy_casecreator_settings.bat` - helper to provision `%LOCALAPPDATA%\CaseCreator` and optional admin settings copy.

### Support/diagnostic scripts (non-primary runtime)
- `rx_fetch_and_parse.py` - diagnostic case-file fetcher/downloader.
- `evo_terminal_probe.py` - CLI probe for Evolution events.
- `test_evo_request.py` - local relay test script with hardcoded credentials/token.
- `manual_import.py` - legacy/manual flow; appears stale (imports missing symbols/signature mismatch).

### Data and templates
- `templates/` - template folders for all route families (`ai_*`, `argen_*`, `itero_*`, `reg_*`), each with XML and most with `Materials.xml`.
- `dr prefs.xml` - very large XML artifact (appears data/reference asset, not actively read by runtime code).

### Duplicate/legacy code area
- `Test scripts/` mirrors core logic files (`case_processor_final_clean.py`, `template_utils.py`, `evo_internal_client.py`, `evo_to_case_data.py`) and appears non-runtime.

### Documentation/planning
- Numerous `*_PLAN.md`, `*_AUDIT.md`, migration notes, UI transition notes.

---

## 3. Entry Points and App Startup Flow

### Primary app startup path (current default)
1. Launcher `launch_importer.bat` executes `pyside6_ui.py` using `py -w`/`pythonw`.
2. `pyside6_ui.py` `main()` creates `QApplication`, `MainWindow`, and enters event loop.
3. `MainWindow.__init__`:
   - initializes queue/thread state,
   - loads UI prefs via `load_local_settings()`,
   - reads app metadata via `get_app_info()`,
   - builds UI widgets and wire-ups.
4. User submits case; UI builds `case_id` with `build_case_id()` and validates via `validate_case_id()`.
5. Queue worker (`ImportWorker` in `QThread`) calls `import_case_by_id()` -> `case_processor_final_clean.process_case_from_id()`.

### Legacy/fallback startup path
1. Launcher `launch_importer_tk_fallback.bat` executes `import_gui.pyw`.
2. `import_gui.pyw` starts both:
   - Flask server thread (`/import-case` on port 5000),
   - Tkinter GUI mainloop.
3. Tk queue worker calls same backend entry (`process_case_from_id` from `case_processor_final_clean.py`).

### Config/service loading behavior
- `config.py` resolves values at import time from:
  - `local_settings.get_setting(...)`,
  - `admin_settings.get_admin_setting(...)`,
  - environment defaults,
  - project-relative fallbacks for `templates` and signature doctor Excel.
- `config.py` also eagerly creates output directories if `CC_IMPORTED_ROOT` is configured.

### Startup branch points
- UI implementation branch (PySide6 primary vs Tk fallback).
- Frozen Windows packaging branch in settings modules (settings location changes to `%LOCALAPPDATA%\CaseCreator`).

---

## 4. UI Architecture

### `pyside6_ui.py`

- **`MainWindow`**
  - Purpose: primary desktop app shell.
  - Reads: local settings, app info, user input case number/year.
  - Triggers: import queue processing, settings saves, advanced settings save, log panel routing.
  - Business logic leakage:
    - hardcoded log-routing classification in `_route_log_panels` (case-summary vs process panel based on exact strings),
    - some import-state/timeout semantics baked into UI.

- **`ImportWorker`**
  - Purpose: background worker object for one import.
  - Reads: one `case_id`.
  - Triggers: backend import call and signal emission.
  - Business logic: none (infrastructure wrapper).

- **`SettingsDialog`**
  - Purpose: edit local settings/UI preferences.
  - Reads initial values from `config.py` constants + main window prefs.
  - Triggers `save_settings_updates` with payload including `EVIDENT_PATH`, `TRIOS_SCAN_ROOT`, `CC_IMPORTED_ROOT`, UI options.
  - Business logic: minimal (year list sanitization/validation only).

- **`AdvancedSettingsDialog`**
  - Purpose: edit admin settings (`EV_INT_BASE`, `EVO_*`, `IMG_*`).
  - Guarded by `current_user_is_admin()` check before opening.
  - Saves via `save_admin_settings_updates`.
  - Business logic: none, but controls sensitive runtime infrastructure.

### `import_gui.pyw` (legacy)

- **`CaseImporterGUI`**
  - Purpose: legacy UI with queue + styled log pane + ngrok probe.
  - Reads: case ID input.
  - Triggers: backend import call, close-protection, optional placeholder advanced settings gate.
  - Business logic leakage:
    - log tag classification includes route semantics,
    - timeout/queue behavior differs from PySide6 path.

- **Flask endpoint `/import-case`**
  - Purpose: API-triggered batch import interface (legacy capability not present in PySide6).
  - Reads `case_ids` from POST JSON.
  - Triggers backend imports and returns log text map.
  - Business logic: no routing rules, but runtime behavior surface exists only in Tk path.

---

## 5. Runtime Flow: End-to-End Processing

### 5.1 Intake
1. UI receives year + case number.
2. `import_service.build_case_id` creates `YYYY-NNNNN`.
3. `import_service.import_case_by_id` delegates to backend entry.

### 5.2 Case folder discovery (`process_case_from_id`)
1. Pull Evolution detail via `get_case_detail_clean(case_id)`.
2. Convert to `case_data` via `build_case_data_from_evo`.
3. Extract patient first/last name.
4. Search `EVIDENT_PATH` portal/date folders newest-first for folder name containing both names.
   - logs `Itero Case` if portal contains `itero`.
   - has fallback for multi-part names using first token + last token.
5. If name search fails, fallback to direct case-number folder match (`== case_id` or startswith).
6. Pass found folder to `process_case(case_id, folder_path, log_callback)`.

### 5.3 Parsing + normalization (`process_case`)
1. Pull fresh Evolution detail again (second API call in full flow).
2. Build normalized `case_data` again.
3. Fail-fast checks:
   - multi-unit cases rejected (manual import required),
   - unsupported material route rejected (manual import required).
4. Populate downstream selection fields:
   - `material` (adz/envision),
   - `shade_usable`,
   - `signature` via signature doctor Excel lookup,
   - scanner inference fallback (`3shape`/`itero`/`sirona` from folder path).

### 5.4 Scanner-source handling
- **3Shape**:
  - locate patient folder under `TRIOS_SCAN_ROOT` with name patterns (`last_first`, `last__first`, optional `(n)` suffix),
  - choose newest by mtime,
  - detect study from `PrePreparationScan.dcm`.
- **iTero**:
  - choose best nested subfolder containing STL files by score (case_id match, parent-name match, STL count).
- **non-3Shape rename pipeline**:
  - collect/copy STL files into `_scan_processing`,
  - classify upper/lower/study by filename keywords,
  - map to `PreparationScan.stl` / `AntagonistScan.stl` / `PrePreparationScan.stl`,
  - return study detection + renamed scan dir.
  - if missing prep scan and patient appears in `JOTFORM_PATH`, return manual Jotform outcome.

### 5.5 Rule evaluation + template selection
1. `template_utils.select_template(case_data)` returns template XML path based on:
   - anterior flag,
   - modeless hint route,
   - `is_ai`,
   - scanner type,
   - signature doctor,
   - material,
   - shade usability and special shade values,
   - doctor-name special cases (Abby Dew and Brier Creek variants).
2. Processor tags case with log classification (`ARGEN`, `DESIGNER`, `SERBIA`, `AI`) based on chosen template and doctor name.

### 5.6 Output route + package generation
1. Destination root is chosen from template filename:
   - `argen*` -> `SEND_TO_ARGEN_PATH`,
   - `*study*`, `*anterior*`, `*ai*` -> `SEND_TO_1_9_PATH` (AI is explicitly rerouted here).
2. Case ID suffixes appended:
   - `os` for Argen template,
   - `i` for iTero scanner.
3. Generate final XML (`generate_final_xml`) by placeholder substitution.
4. Copy template-side assets (`Materials.xml`, optional `Manufacturers.3ml`).
   - If Argen template and shade exists, inject shade token into `Materials.xml`.
5. Copy Rx PDF if present (matching patient last name).
6. Copy scans into final 3Shape structure.
7. Optional zip only when `should_zip(...)` says modeless Argen case.
8. On exception, write failure marker text file under `FAILED_IMPORT_PATH`.

### 5.7 Logging/readback
- Backend emits plain messages through callback.
- UI classifies/render messages; PySide6 additionally splits into Summary vs Process panel based on exact message patterns.

---

## 6. File-by-File Responsibility Map

### Primary runtime files

- `pyside6_ui.py`
  - Responsibility: primary UI, queue orchestration, settings dialogs, log rendering/routing.
  - Key classes: `MainWindow`, `ImportWorker`, `SettingsDialog`, `AdvancedSettingsDialog`.
  - Depends on: `import_service`, `config`, `local_settings`, `admin_settings`, `admin_access`.
  - Type: UI + infrastructure glue (mixed).
  - Stability: medium; lots of hardcoded UI/log routing strings.
  - Hardcoded rules: log-message classification lists, default years/themes/logos.

- `import_gui.pyw`
  - Responsibility: legacy Tk UI + embedded Flask endpoint.
  - Key classes/functions: `CaseImporterGUI`, `import_case` route.
  - Depends on: `case_processor_final_clean`, Flask, Tkinter.
  - Type: UI + small service surface.
  - Stability: low-to-medium (legacy path retained for fallback).
  - Hardcoded rules: tag detection and route string coloring.

- `import_service.py`
  - Responsibility: thin adapter to backend.
  - Key functions: `import_case_by_id`, `validate_case_id`, `build_case_id`, `get_app_info`.
  - Depends on: `case_processor_final_clean`.
  - Type: service facade.
  - Stability: high (small and simple).
  - Hardcoded rules: permissive validation (non-empty only), app name/version placeholder.

- `case_processor_final_clean.py`
  - Responsibility: central processor and orchestration pipeline.
  - Key functions: `process_case_from_id`, `process_case`, `rename_scans`, `generate_final_xml`, `should_zip`, `is_case_in_jotform`.
  - Depends on: `evo_internal_client`, `evo_to_case_data`, `template_utils`, `config`.
  - Type: business logic + infrastructure + file operations (highly mixed).
  - Stability: fragile/high-risk due to size and many conditional branches.
  - Hardcoded rules: extensive (scanner keywording, route enforcement, destination mapping, doctor exceptions, output suffixes, material allowlist, Jotform behavior).

- `template_utils.py`
  - Responsibility: template decision matrix + helper predicates + material mapping + shade inject utility.
  - Key functions: `select_template`, `is_signature_doctor`, `is_abby_dew`, `is_vd_brier_creek`, `is_non_argen_shade`, `map_material_to_xml`.
  - Depends on: `config`, `pandas/openpyxl`.
  - Type: business rule core + helper.
  - Stability: fragile because decision tree is long and order-sensitive.
  - Hardcoded rules: very high (doctor names, shade rules, template folder mapping).

- `evo_to_case_data.py`
  - Responsibility: transform parsed Evolution payload into normalized case_data and hints.
  - Key functions: `build_case_data_from_evo`, shade conversion/pick helpers, route/model/material extractors.
  - Depends on: stdlib only.
  - Type: business transformation logic.
  - Stability: medium; clear helpers but includes behavior toggles.
  - Hardcoded rules: shade conversion table, shade ordering, route descriptors, `DISABLE_MODELESS=True`.

- `evo_internal_client.py`
  - Responsibility: call Evolution internal endpoint and hand response to parser.
  - Key function: `get_case_detail_clean`.
  - Depends on: `requests`, `evolution_case_detail`.
  - Type: infrastructure/API client.
  - Stability: medium.
  - Hardcoded values: default base URL and credentials in module-level env fallbacks.

- `evolution_case_detail.py`
  - Responsibility: parse Evolution XML response into structured dict.
  - Key function: `parse_get_case_detail`.
  - Depends on: `xml.etree`, regex, datetime.
  - Type: infrastructure/parser.
  - Stability: medium-high (pure parse logic).
  - Hardcoded rules: XML field mapping and date format assumptions.

- `config.py`
  - Responsibility: runtime settings resolution and derived destination paths.
  - Depends on: `local_settings`, `admin_settings`.
  - Type: configuration/infrastructure.
  - Stability: medium; import-time side effects create directories.
  - Hardcoded rules: destination folder names, debug flag false.

- `local_settings.py` / `admin_settings.py`
  - Responsibility: JSON settings load/cache/merge-save with packaged path behavior.
  - Type: infrastructure/persistence.
  - Stability: high.
  - Hardcoded rules: `%LOCALAPPDATA%\CaseCreator` path when frozen on Windows.

- `admin_access.py`
  - Responsibility: Windows admin-rights check.
  - Type: infrastructure/security gate.
  - Stability: high/simple.

### Secondary/diagnostic or legacy files
- `manual_import.py` - legacy/manual flow; appears stale (imports undefined `unzip_3oxz`, calls `process_case` with wrong signature).
- `rx_fetch_and_parse.py` - diagnostic fetch script with multiple auth attempts.
- `evo_terminal_probe.py` - Evolution raw XML probe CLI.
- `test_evo_request.py` - local relay testing script with hardcoded credentials/token.
- `Test scripts/*` - duplicate variants of key modules, likely non-runtime.

---

## 7. Business Rule Inventory

### 7.1 Doctor-name based rules

1. **Abby Dew override**
   - Location: `template_utils.is_abby_dew`, used in `template_utils.select_template`.
   - Input: doctor name contains both `"abby"` and `"dew"`.
   - Action: prevents Argen branch in shade-usable non-signature non-study paths; routes to AI templates.
   - Duplication: doctor-based routing also appears in processor (`brier creek` checks), but Abby logic is template-only.
   - Config candidate: yes (keyword rule list).

2. **Brier Creek / Serbia override**
   - Location: `template_utils.is_vd_brier_creek`; plus separate `is_serbia_case = "brier creek" in doctor_name.lower()` in `case_processor_final_clean.process_case`.
   - Input: doctor name contains location and in one helper also specific last names (`britt`, `de frias`, `escobar`, `martin`).
   - Action:
     - template selection branches away from Argen in some combinations,
     - log-level route label switches between designer vs Serbia.
   - Duplication: yes (two different definitions/strictness).
   - Config candidate: very strong.

3. **Signature doctor list**
   - Location: `template_utils.is_signature_doctor`.
   - Input: exact `Dr. {doctor_name}` membership in Excel `Name` column.
   - Action: influences template family in non-study cases.
   - Duplication: computed in processor and consumed by template selector.
   - Config candidate: yes (external data source already exists).

### 7.2 Shade-based rules

1. **Shade normalization/conversion**
   - Location: `evo_to_case_data.py` (`_SHADE_CONVERSIONS`, `_SHADE_ORDER`, `_pick_single_shade`).
   - Input: raw shade string(s) from services.
   - Action: tokenize, remove Vita prefix, convert BL/3D Master, dedupe, pick lightest.
   - Duplication: none obvious.
   - Config candidate: yes (mapping table + priority order).

2. **Non-Argen shade trigger**
   - Location: `template_utils.is_non_argen_shade`.
   - Input: shade contains `C3` or `A4`.
   - Action: steers non-study non-signature cases away from Argen to AI variants.
   - Duplication: no.
   - Config candidate: yes (threshold/denylist set).

3. **Shade usability flag**
   - Location: `case_processor_final_clean.process_case`.
   - Input: any non-empty shade.
   - Action: broad branch control in template matrix.
   - Duplication: no.
   - Config candidate: maybe (rule-policy choice).

### 7.3 Material-based rules

1. **Allowed route/material gate**
   - Location: `case_processor_final_clean.process_case`.
   - Input: `material_hint.route`.
   - Condition: only `argen_envision`, `argen_adzir`, `modeless` allowed.
   - Action: reject to manual import for others.
   - Duplication: related route logic in `evo_to_case_data`.
   - Config candidate: yes.

2. **Material extraction from service descriptions**
   - Location: `evo_to_case_data._material_from_services`.
   - Input: service description keywords (`adzir`, `argenz`, `envision`).
   - Action: sets `material` (`adz`/`envision`) used downstream.
   - Config candidate: yes (keyword map).

### 7.4 Scanner-based rules

1. **Scanner inference from folder path**
   - Location: `case_processor_final_clean.process_case` (multiple sections).
   - Input: folder path text containing `3shape`, `itero`, `sirona`.
   - Action: decides scanner branch and scan-handling path.
   - Duplication: scanner assignment happens twice in same function.
   - Config candidate: likely internal; keep code, but centralize.

2. **3Shape folder matching heuristic**
   - Location: `case_processor_final_clean.process_case`.
   - Input: normalized patient name patterns + numbered suffix support.
   - Action: picks newest matching patient folder under `TRIOS_SCAN_ROOT`.
   - Config candidate: limited (pattern conventions may need editability).

3. **iTero nested folder scoring**
   - Location: `case_processor_final_clean.process_case`.
   - Input: nested subfolders with STLs, case id in name, STL count.
   - Action: selects best scan source subfolder.
   - Config candidate: maybe (weights, preferred indicators).

### 7.5 Study-model/contact-model rules

1. **Study detection keywords for STLs**
   - Location: `case_processor_final_clean.STUDY_SCAN_KEYWORDS`.
   - Action: classify study scan and set `has_study`.
   - Config candidate: yes.

2. **3Shape study detection by DCM filenames**
   - Location: `case_processor_final_clean.process_case`.
   - Input: existence of `Upper/PrePreparationScan.dcm` or `Lower/PrePreparationScan.dcm`.
   - Action: set `has_study`.
   - Config candidate: maybe.

3. **Modeless contact model behavior**
   - Location: `template_utils.select_template` modeless templates; plus `evo_to_case_data` toggle.
   - Action: routes to `argen_modeless_*` templates (currently effectively disabled by toggle).
   - Config candidate: strong.

### 7.6 Destination/output path rules

1. **Template filename -> destination root**
   - Location: `case_processor_final_clean.process_case`.
   - Action:
     - `argen` => `SEND_TO_ARGEN_PATH`,
     - `study`/`anterior`/`ai` => `SEND_TO_1_9_PATH`.
   - Note: AI path constant exists but AI currently routed to designer path.
   - Config candidate: yes.

2. **Serbia vs designer labels**
   - Location: `case_processor_final_clean.process_case`.
   - Input: doctor contains `brier creek`.
   - Action: log label changes only (not destination path change in current code).
   - Config candidate: yes.

3. **Case ID suffix rules**
   - Location: `case_processor_final_clean.process_case`.
   - Action: append `os` for Argen template, `i` for iTero.
   - Config candidate: yes.

### 7.7 Argen/no-Argen and model/no-model decisions

1. **Anterior cannot be sent to Argen**
   - Location: `template_utils.select_template`.
   - Condition: `is_anterior and not has_study`.
   - Action: force `itero_*_anterior` or `reg_*_anterior`.
   - Config candidate: yes.

2. **Modeless gating toggle**
   - Location: `evo_to_case_data.DISABLE_MODELESS = True`.
   - Condition: modeless route only active if toggle false.
   - Action: route remains model path while disabled.
   - Config candidate: yes (mode flag).

3. **Zip behavior for modeless Argen**
   - Location: `case_processor_final_clean.should_zip`.
   - Action: zip + remove folder only for modeless family + Argen.
   - Config candidate: yes.

### 7.8 Fallback/default rules

1. **Manual import outcomes**
   - Multi-unit reject, unsupported material reject, Jotform fallback in missing scan cases.
   - Location: `case_processor_final_clean.process_case`.

2. **Name-based search fallback to case-number search**
   - Location: `case_processor_final_clean.process_case_from_id`.

3. **Date and due-date fallback**
   - Location: `generate_final_xml`.
   - Delivery timestamp falls back to create timestamp if parse invalid or in past.

---

## 8. Template Selection Logic Audit

### Where template decisions are made
- Primary: `template_utils.select_template(case_data)`.
- Inputs prepared in `case_processor_final_clean.process_case` and `evo_to_case_data.build_case_data_from_evo`.

### Inputs that influence selection
- `is_anterior`
- `has_study`
- `scanner` (`itero` vs non-itero)
- `signature`
- `material` (`adz` vs non-adz)
- `shade_usable`
- shade content (`C3`/`A4` special)
- doctor flags (`abby+dew`, brier creek set)
- `is_ai` (currently always false in `build_case_data_from_evo`)
- `material_hint.route` (`modeless` path support)

### Scattering characteristics
- Decision engine itself is centralized in one function, but **input derivation is scattered**:
  - shade normalization in `evo_to_case_data`,
  - signature computation in processor via external Excel,
  - scanner inference in processor,
  - doctor special checks in template utils and processor.

### Condition complexity notes
- `select_template` is a long ordered `if/elif` chain; order materially affects behavior.
- Some branches are effectively dormant (e.g., `is_ai` likely false unless set externally).
- Serbia-related logic appears both strict (helper with name+location) and loose (`brier creek` substring only).

### Downstream dependencies
- Template filename later controls destination root and route logging.
- Template directory supplies auxiliary assets (`Materials.xml`, optional `Manufacturers.3ml`).
- Argen template selection affects shade injection and potential zip logic.

---

## 9. Output Path / Destination Routing Audit

### Path decision locations
- `config.py` derives root destinations from `CC_IMPORTED_ROOT`.
- `case_processor_final_clean.process_case` decides per-case `target_root` based on template filename.

### Data that influences path selection
- Selected template filename (`argen`, `study`, `anterior`, `ai` substrings).
- Case ID suffix rules (`os`, `i`) modify final folder names.
- Modeless+Argen determines zip-vs-folder output.

### Defaults and overrides
- Default destination roots are empty unless `CC_IMPORTED_ROOT` configured.
- AI path exists in config (`SEND_TO_AI_PATH`) but current runtime intentionally routes AI templates to `SEND_TO_1_9_PATH`.
- Serbia logic only changes log labels; no separate filesystem destination currently implemented.

### Argen/model/no-model handling
- Argen templates always routed to `SEND_TO_ARGEN_PATH`.
- Non-argen study/anterior/AI templates routed to `SEND_TO_1_9_PATH`.
- Modeless currently effectively disabled at case-data stage; if enabled, modeless Argen can trigger zip behavior.

### Centralization assessment
- Core destination assignment is localized in one processor block, but it relies on indirect template naming conventions and external template chooser state, making rule tracing cross-file.

---

## 10. Current Config and Settings Audit

### Settings mechanisms

1. **Local settings (`local_settings.py`)**
   - File: `local_settings.json`.
   - Location:
     - normal script mode: repo directory,
     - frozen Windows mode: `%LOCALAPPDATA%\CaseCreator`.
   - Controls:
     - paths: `EVIDENT_PATH`, `TRIOS_SCAN_ROOT`, `CC_IMPORTED_ROOT`, optional legacy keys,
     - UI preferences: theme/logo/color mode/title/subtitle/year options/default year.

2. **Admin settings (`admin_settings.py`)**
   - File: `admin_settings.json`.
   - Same location behavior as local settings.
   - Controls:
     - Evolution API base/creds,
     - image server creds,
     - optional admin-only path keys like `JOTFORM_PATH`.

3. **Environment fallback**
   - `config.py` and `evo_internal_client.py` use env vars and in one case hardcoded defaults.

### Existing settings UIs
- `SettingsDialog` in `pyside6_ui.py` writes local settings.
- `AdvancedSettingsDialog` in `pyside6_ui.py` writes admin settings (admin-gated).
- Tk UI has only placeholder advanced settings hook.

### Runtime control behavior
- Many values from settings directly influence runtime behavior (`EVIDENT_PATH`, `TRIOS_SCAN_ROOT`, output roots, API credentials).
- Many business rules remain hardcoded despite settings pages (doctor keywords, shade thresholds, template mapping logic, destination rules).

---

## 11. Hardcoded Values and Scattered Decision Points

Important hardcoded elements:

- Doctor keywords and names:
  - `abby`, `dew`,
  - Brier Creek location + specific last names list.
- Shade conditions:
  - non-Argen triggers include `C3`, `A4`,
  - large hardcoded shade conversion map and rank order.
- Route/material keyword matching in service descriptions:
  - `envision`, `adzir`, `argenz`, `emax zirconia`, manual-import hints (`gold`, `alloy`, `pfm`, etc.).
- Toggle:
  - `DISABLE_MODELESS = True` in `evo_to_case_data.py`.
- Scanner/file naming heuristics:
  - keyword lists for upper/lower/study/prep/antagonist.
- Destination mapping by template filename substrings.
- Output folder naming:
  - suffix `_os`, `_i`.
- UI log classification:
  - exact message string whitelists in `pyside6_ui.py`.
- Route labels:
  - Serbia/designer determination by `"brier creek"` substring.

Why this matters:
- These values are likely business-changeable and currently difficult to edit safely because they are embedded across parser, processor, template selector, and UI.

---

## 12. Cross-File Coupling and Fragility Points

1. **Template decision coupling across 3 files**
   - `evo_to_case_data` computes hints,
   - processor mutates/augments fields,
   - `template_utils` branches on final combined state.
   - Risk: changing one file silently shifts branch behavior.

2. **Doctor/location rule duplication**
   - Serbia logic implemented differently in processor and template utils.
   - Risk: mismatch between selected template and labeled route.

3. **UI tied to backend log text contracts**
   - `pyside6_ui._route_log_panels` relies on exact message strings.
   - Risk: harmless log wording edits break UI summary/process splitting.

4. **Config side effects at import time**
   - `config.py` creates output directories during import.
   - Risk: implicit filesystem side effects and startup-order dependency.

5. **Legacy/stale modules in runtime tree**
   - `manual_import.py` appears out-of-sync with processor signatures.
   - Duplicate `Test scripts/` mirror core modules.
   - Risk: future edits applied to wrong copy.

6. **API client credential source inconsistency**
   - `config.py` supports admin settings, but `evo_internal_client.py` currently reads env/default literals directly.
   - Risk: advanced settings may not affect all code paths as expected.

---

## 13. Packaging-Sensitive Areas

1. **Settings persistence path switch**
   - `local_settings.py` and `admin_settings.py` switch to `%LOCALAPPDATA%\CaseCreator` only when frozen on Windows.

2. **Bundled resource assumptions**
   - `config.py` default `TEMPLATE_DIR` and signature doctor Excel path are relative to module directory.
   - `build_pyside6_onefolder.bat` explicitly includes `templates/` and `List of Signature Dr.xlsx`.

3. **Filesystem roots required at runtime**
   - `EVIDENT_PATH`, `TRIOS_SCAN_ROOT`, `CC_IMPORTED_ROOT` must be valid for production behavior.

4. **Absolute/default network assumptions**
   - Evolution/internal endpoints and image server access depend on LAN/reachable addresses and credentials.

5. **Large asset files**
   - template `Materials.xml` files are huge and placeholder-driven; copying/injection is performance and packaging relevant.

6. **Working-directory and launcher assumptions**
   - `.bat` launchers `pushd` into fixed project directory for source mode.

---

## 14. Candidate “Future Exposed Rule” Inventory

### Doctor keyword routing rules
- Candidate: Abby Dew and Brier Creek/Serbia conditions.
- Why configurable: operational routing exceptions are business-driven and likely to change.
- Current touches: `template_utils.py`, `case_processor_final_clean.py`.
- Potential config type: rule list with match conditions + route effect.

### Shade/template rules
- Candidate: non-Argen shade list, shade conversion map, shade priority order.
- Why configurable: clinical/material policy evolves.
- Current touches: `evo_to_case_data.py`, `template_utils.py`.
- Potential config type: mapping table + threshold/denylist.

### Template mapping matrix
- Candidate: long `if/elif` tree in `select_template`.
- Why configurable: currently business policy encoded as code order.
- Current touches: `template_utils.py` (+ inputs from processor).
- Potential config type: structured rule table with explicit precedence.

### Destination selection toggles
- Candidate: template-filename -> destination root mapping, AI reroute to designer, suffixing rules.
- Why configurable: workflow routing often changes by operations.
- Current touches: `case_processor_final_clean.py`, `config.py`.
- Potential config type: destination mapping table + mode flags.

### Argen/model/modeless behavior switches
- Candidate: `DISABLE_MODELESS`, modeless zip policy, material allowlist.
- Why configurable: program-state/tactical policy controls.
- Current touches: `evo_to_case_data.py`, `case_processor_final_clean.py`.
- Potential config type: boolean toggles + allowlist.

### Scanner/file-classification heuristics
- Candidate: study/prep/antagonist keyword lists and iTero scoring.
- Why configurable: scanner export naming conventions vary by source.
- Current touches: `case_processor_final_clean.py`.
- Potential config type: keyword lists + scoring weights.

### Manual-import gate conditions
- Candidate: multi-unit reject policy and unsupported-material reject policy.
- Why configurable: process acceptance criteria may change.
- Current touches: `case_processor_final_clean.py`.
- Potential config type: policy toggles and material family allowlist.

---

## 15. Recommended No-Behavior-Change Reorganization Plan

1. **Create explicit domain boundary (no logic change)**
   - Keep current decisions but move them into dedicated modules:
     - `domain/case_rules.py` (template/output/manual policies),
     - `domain/scanner_intake.py` (folder/scan normalization),
     - `domain/case_mapper.py` (EVO -> case data).

2. **Preserve current rule order exactly**
   - Lift `select_template` branches into data/objects while preserving branch precedence and outputs.

3. **Separate orchestration from operations**
   - Keep `process_case` as orchestrator only; move file-copy/xml/zip helpers into `infrastructure/packaging.py`.

4. **Stabilize contract between backend and UI**
   - Replace fragile free-form log text matching with structured event codes while still emitting existing text for compatibility.

5. **Unify config source behavior**
   - Route all API/path credential reads through one config provider layer.

6. **Mark non-runtime code explicitly**
   - Fence off legacy/test/probe scripts from production import path and document them as tooling-only.

7. **Defer config externalization**
   - First centralize rules in code modules, then expose selected rules gradually to JSON.

---

## 16. Suggested Future Folder Architecture

```text
case_creator/
  app/
    ui/
      pyside6_main.py
      tk_legacy.py
    services/
      import_service.py
      worker_events.py
  domain/
    case_data/
      evo_mapper.py
      shade_normalization.py
    rules/
      template_rules.py
      destination_rules.py
      doctor_rules.py
      material_rules.py
      scanner_rules.py
    pipeline/
      process_case.py
      find_case_folder.py
  infrastructure/
    evo/
      client.py
      parser.py
    fs/
      scan_ops.py
      package_ops.py
    config/
      settings_provider.py
      local_settings_store.py
      admin_settings_store.py
  assets/
    templates/
    signature_doctors/
  tools/
    evo_terminal_probe.py
    rx_fetch_and_parse.py
    test_evo_request.py
```

Notes:
- Keep behavior-preserving wrappers for existing import paths during migration.
- Keep template assets unchanged; only relocate with path adapter if needed.
- Keep launcher compatibility while swapping implementation internals.

---

## 17. Open Questions / Unclear Areas

1. Is `manual_import.py` intentionally deprecated, or still used in a hidden workflow? It appears incompatible with current processor signatures/imports.
2. Should Serbia currently change filesystem destination or only log labeling? Current code suggests label-only.
3. Is `is_ai` ever set externally in production? Current mapper defaults to `False`, making AI branches potentially unreachable except via other conditions.
4. Which of `Test scripts/*` files are authoritative for future edits vs archival copies?
5. Are there packaged-runtime code paths still using `evo_internal_client.py` defaults instead of admin settings values?
6. Is `dr prefs.xml` consumed by any external process or retained as historical artifact?

---

## 18. Appendix: Rule and Decision Index

| Rule / Decision | File | Function/Class | Input checked | Output changed | Notes |
|---|---|---|---|---|---|
| Case ID build | `import_service.py` | `build_case_id` | year + case number | formatted case id | UI-facing behavior contract |
| Name-based case folder search | `case_processor_final_clean.py` | `process_case_from_id` | first/last name in folder names | chosen source folder | newest-first across portal/date folders |
| Multi-part name fallback | `case_processor_final_clean.py` | `find_evident_folder_by_name` nested helper | tokenized first/last | fallback folder match | handles middle names/parentheses |
| Legacy case-number fallback | `case_processor_final_clean.py` | `process_case_from_id` | folder equals/startswith case id | source folder | fallback if name search fails |
| Multi-unit rejection | `case_processor_final_clean.py` | `process_case` | services tooth set / units >1 | manual import return | hard fail-fast gate |
| Material allowlist rejection | `case_processor_final_clean.py` | `process_case` | `material_hint.route` | manual import return | allowed: argen_envision/adzir/modeless |
| Modeless enable toggle | `evo_to_case_data.py` | module const + `build_case_data_from_evo` | `DISABLE_MODELESS` | route/model_mode hints | currently disabled (`True`) |
| Material parse from services | `evo_to_case_data.py` | `_material_from_services` | description keywords | `material_hint.material` | adz vs envision |
| Route parse from services | `evo_to_case_data.py` | `_route_from_services` | description keywords | `material_hint.route` | regular/argen_* route family |
| Shade conversion | `evo_to_case_data.py` | `_pick_single_shade` | raw shade strings | normalized single shade | conversion + dedupe + lightest |
| Signature doctor detection | `template_utils.py` | `is_signature_doctor` | Excel name match | `case_data.signature` usage | external data dependency |
| Abby Dew predicate | `template_utils.py` | `is_abby_dew` | doctor string contains both tokens | template branching | special business override |
| Brier Creek predicate | `template_utils.py` | `is_vd_brier_creek` | last-name list + location | template branching | stricter than processor label rule |
| Non-Argen shade predicate | `template_utils.py` | `is_non_argen_shade` | shade contains C3/A4 | template branching | shade-driven exception |
| Template selection matrix | `template_utils.py` | `select_template` | combined case_data flags | template folder/xml path | primary rule engine |
| Anterior non-Argen enforcement | `template_utils.py` | `select_template` | `is_anterior and not has_study` | anterior template path | explicit Argen block |
| Scanner inference fallback | `case_processor_final_clean.py` | `process_case` | folder path tokens | scanner mode | set twice in function |
| 3Shape patient folder heuristic | `case_processor_final_clean.py` | `process_case` | patient name patterns + mtime | scan source folder | supports `_` and `__` naming |
| iTero nested folder scoring | `case_processor_final_clean.py` | `process_case` | case id/name/STL count | chosen scan folder | heuristic scoring |
| STL study/prep/antagonist classification | `case_processor_final_clean.py` | `rename_scans` | scan filename keywords | scan role assignment | keyword-driven |
| Jotform fallback | `case_processor_final_clean.py` | `process_case` + `is_case_in_jotform` | missing scans + name in Jotform path | manual import return | admin path dependency |
| Destination root map | `case_processor_final_clean.py` | `process_case` | template filename substrings | `target_root` selection | AI currently to designer path |
| Serbia/designer labeling | `case_processor_final_clean.py` | `process_case` | doctor contains `brier creek` | log route message | label-only in current code |
| Case suffix mapping | `case_processor_final_clean.py` | `process_case` | template type + scanner | case_id suffix (`os`, `i`) | affects output naming |
| Modeless zip decision | `case_processor_final_clean.py` | `should_zip` + `process_case` | route/modeless + Argen target/template | zip vs folder output | removes unzipped output after zip |
| Materials shade injection | `template_utils.py` + `case_processor_final_clean.py` | `inject_shade_into_materials` caller block | Argen template + non-empty shade | rendered `Materials.xml` | placeholder substitution |
| XML placeholder substitution | `case_processor_final_clean.py` | `generate_final_xml` | case fields + generated IDs | final case XML | includes comments sanitization |
| Output failure marker | `case_processor_final_clean.py` | `process_case` exception path | caught exception | file in `FAILED_IMPORT_PATH` | preserves failure trace |
| UI log panel routing | `pyside6_ui.py` | `_route_log_panels` | exact message text patterns | summary vs process log placement | tightly coupled to backend text |

