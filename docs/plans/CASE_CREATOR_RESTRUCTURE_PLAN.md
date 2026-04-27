# CASE CREATOR RESTRUCTURE PLAN

## 1. Goals

### Goals
- Reorganize the codebase into clear layers (UI, domain rules, orchestration, infrastructure, tooling) without changing runtime behavior.
- Centralize business-changeable rule families into dedicated code modules (still code-first).
- Reduce cross-file coupling by defining stable boundaries between:
  - case-data normalization,
  - rule evaluation,
  - scanner intake/file ops,
  - XML/output packaging,
  - UI/service adapters.
- Preserve current deployment model (Windows source launch + PyInstaller one-folder packaging assumptions).
- Enable later config externalization by first creating well-scoped rule seams.

### Non-goals (this restructure phase)
- No behavior changes.
- No routing/template precedence changes.
- No destination policy changes.
- No new settings/admin UI surfaces.
- No conversion to JSON-driven rules yet.
- No feature expansion.

---

## 2. Behavior Preservation Contract

The following behavior is locked and must remain exactly compatible during restructure:

1. **Template precedence order**
   - `template_utils.select_template` branch order is authoritative.
   - Anterior/non-study branch precedence must remain first.
   - Any dormant branches (e.g., `is_ai`) must remain logically identical.

2. **Doctor/shade overrides**
   - Abby/Dew exceptions remain exact-string-substring based.
   - Brier Creek/Serbia handling remains as implemented today (including current strict/loose split between modules).
   - Non-Argen shade checks (`C3`, `A4`) remain unchanged.
   - Signature-doctor lookup behavior remains Excel-driven and exact-match compatible.

3. **Destination routing behavior**
   - Template filename substring mapping to destination root remains unchanged.
   - AI template reroute to `SEND_TO_1_9_PATH` remains unchanged.
   - Case suffix behavior (`_os`, `_i`) remains unchanged.
   - Serbia/designer labels remain log-compatible.

4. **Argen/modeless/contact-model behavior (current state)**
   - Current modeless effective behavior remains unchanged (`DISABLE_MODELESS` semantics preserved).
   - Current zip policy (`should_zip`) remains unchanged.
   - Argen materials/shade injection behavior remains unchanged.

5. **Scanner folder discovery behavior**
   - Name-based `EVIDENT_PATH` search and fallback by case number remain unchanged.
   - 3Shape folder heuristics (`last_first`, `last__first`, `(n)` suffix, newest mtime) remain unchanged.
   - iTero nested STL scoring behavior remains unchanged.
   - STL keyword classification and fallback assignment behavior remains unchanged.

6. **Manual-import behavior**
   - Multi-unit gate behavior and message compatibility remain unchanged.
   - Unsupported-material gate behavior and messages remain unchanged.
   - Jotform fallback behavior remains unchanged.

7. **Current log text compatibility**
   - Existing backend log text strings remain unchanged.
   - PySide6 summary/process panel routing compatibility must be preserved.
   - Tk fallback log/tag behavior remains compatible.

8. **Settings persistence behavior**
   - Existing local/admin settings keys and merge semantics remain unchanged.
   - Existing settings dialogs continue to read/write same keys.
   - No key renames in this phase.

9. **Frozen/packaged behavior**
   - `%LOCALAPPDATA%\CaseCreator` behavior in frozen mode remains unchanged.
   - Packaging-required assets (`templates/`, signature Excel) and relative lookup assumptions remain unchanged.
   - Launcher behavior remains unchanged until explicitly migrated later.

---

## 3. Proposed Future Source Architecture

```text
src/
  case_creator/
    app/
      ui/
        pyside6_main_window.py
        pyside6_settings_dialogs.py
        pyside6_worker.py
        tk_legacy_window.py
        log_routing_contract.py
      services/
        import_service.py
        app_info.py

    domain/
      case_data/
        evolution_case_mapper.py
        shade_normalization.py
        material_hint_extraction.py
      rules/
        doctor_rules.py
        shade_rules.py
        material_rules.py
        template_rules.py
        destination_rules.py
        scanner_rules.py
        manual_review_rules.py
        naming_rules.py
      decisions/
        template_selector.py
        destination_selector.py
        manual_review_selector.py
      contracts/
        case_models.py
        decision_models.py

    pipeline/
      import_pipeline.py
      case_folder_locator.py
      scanner_intake_pipeline.py
      xml_generation_pipeline.py
      output_packaging_pipeline.py
      failure_pipeline.py

    infrastructure/
      evolution/
        client.py
        parser.py
      fs/
        scan_file_ops.py
        copy_ops.py
        archive_ops.py
        path_ops.py
      config/
        settings_provider.py
        local_settings_store.py
        admin_settings_store.py
        runtime_config.py
      templates/
        template_asset_loader.py
        materials_injector.py

    compat/
      legacy_api.py
      legacy_log_strings.py

tools/
  evo_terminal_probe.py
  rx_fetch_and_parse.py
  test_evo_request.py
  legacy_manual_import.py
  duplicate_test_scripts/

entrypoints/
  pyside6_ui.py
  import_gui.pyw
  import_service.py
  config.py
```

Notes:
- `entrypoints/` represents compatibility wrappers preserving old import paths during migration.
- Runtime behavior remains anchored by compatibility wrappers until all call sites are moved.

---

## 4. Current-to-Future Mapping

- `pyside6_ui.py`
  - Action: **split + wrap**
  - Future role: UI shell + worker wiring; settings dialogs and log contract extracted into dedicated modules.

- `import_gui.pyw`
  - Action: **keep as-is initially, then isolate as legacy**
  - Future role: compatibility fallback entrypoint (`tk_legacy_window.py`) with minimal backend wrapper.

- `import_service.py`
  - Action: **move with thin compatibility wrapper**
  - Future role: stable service facade under `app/services/import_service.py`.

- `case_processor_final_clean.py`
  - Action: **split progressively**
  - Future role: replaced by `pipeline/import_pipeline.py` + domain/infrastructure modules; legacy wrapper preserved for old imports.

- `template_utils.py`
  - Action: **split**
  - Future role:
    - `domain/decisions/template_selector.py`
    - `domain/rules/*` modules
    - template utility helpers in infrastructure/templates.

- `evo_to_case_data.py`
  - Action: **split**
  - Future role:
    - `domain/case_data/evolution_case_mapper.py`
    - `domain/case_data/shade_normalization.py`
    - `domain/case_data/material_hint_extraction.py`.

- `evo_internal_client.py`
  - Action: **move + normalize config access**
  - Future role: `infrastructure/evolution/client.py` using unified settings provider.

- `evolution_case_detail.py`
  - Action: **move**
  - Future role: `infrastructure/evolution/parser.py`.

- `config.py`
  - Action: **wrap + decompose**
  - Future role: compatibility facade over `infrastructure/config/runtime_config.py`.

- `local_settings.py` / `admin_settings.py`
  - Action: **move**
  - Future role: `infrastructure/config/*_store.py` with identical behavior.

- `admin_access.py`
  - Action: **move**
  - Future role: `infrastructure/config/admin_access.py` (or `app/security/admin_access.py`).

- `manual_import.py`
  - Action: **isolate as legacy/tooling**
  - Future role: move to `tools/legacy_manual_import.py`, not in primary runtime path.

- `Test scripts/*`
  - Action: **isolate**
  - Future role: `tools/duplicate_test_scripts/` with clear non-authoritative label.

- `evo_terminal_probe.py`, `rx_fetch_and_parse.py`, `test_evo_request.py`
  - Action: **isolate as tooling**
  - Future role: `tools/` with explicit runtime exclusion.

- `launch_importer.bat`, `launch_importer_tk_fallback.bat`, `build_pyside6_onefolder.bat`, `deploy_casecreator_settings.bat`
  - Action: **keep as-is initially**
  - Future role: update only after entrypoint wrappers are stable.

---

## 5. Rule Centralization Plan

### A. Doctor rules
- Current locations:
  - `template_utils.is_abby_dew`
  - `template_utils.is_vd_brier_creek`
  - processor inline `"brier creek"` checks
  - `is_signature_doctor`
- Proposed module: `domain/rules/doctor_rules.py`
- Future config candidate: **yes**
- Status target: centralized internal code table first.

### B. Shade rules
- Current locations:
  - `evo_to_case_data` shade conversion/order/tokenization
  - `template_utils.is_non_argen_shade`
  - processor `shade_usable`
- Proposed modules:
  - `domain/case_data/shade_normalization.py`
  - `domain/rules/shade_rules.py`
- Future config candidate: **yes**

### C. Material rules
- Current locations:
  - `evo_to_case_data._material_from_services`, `_route_from_services`
  - processor allowlist/manual gate
- Proposed module: `domain/rules/material_rules.py`
- Future config candidate: **yes**

### D. Template rules
- Current locations:
  - `template_utils.select_template`
- Proposed modules:
  - `domain/rules/template_rules.py` (rule definitions)
  - `domain/decisions/template_selector.py` (evaluation order engine)
- Future config candidate: **yes** (later table externalization)

### E. Destination rules
- Current locations:
  - processor template filename -> destination root mapping
  - Serbia/designer labeling block
- Proposed modules:
  - `domain/rules/destination_rules.py`
  - `domain/decisions/destination_selector.py`
- Future config candidate: **yes**

### F. Scanner rules
- Current locations:
  - processor scanner inference
  - `rename_scans` keyword classification
  - 3Shape/iTero folder heuristics
- Proposed module: `domain/rules/scanner_rules.py`
- Future config candidate: **partial** (keywords/scores likely configurable)

### G. Manual-review rules
- Current locations:
  - processor multi-unit gate
  - unsupported material gate
  - Jotform fallback logic
- Proposed modules:
  - `domain/rules/manual_review_rules.py`
  - `domain/decisions/manual_review_selector.py`
- Future config candidate: **yes**

### H. Naming/suffix rules
- Current locations:
  - processor case suffix (`os`, `i`)
  - output folder naming conventions
- Proposed module: `domain/rules/naming_rules.py`
- Future config candidate: **yes**

---

## 6. Processor Decomposition Plan

Target decomposition of `case_processor_final_clean.py` (no behavior change):

1. **Orchestration responsibilities**
   - New: `pipeline/import_pipeline.py`
   - Keeps current top-level flow order and logging semantics.

2. **Folder discovery responsibilities**
   - New: `pipeline/case_folder_locator.py`
   - Contains current `process_case_from_id` folder search logic unchanged.

3. **Scanner intake/rename responsibilities**
   - New:
     - `pipeline/scanner_intake_pipeline.py`
     - `infrastructure/fs/scan_file_ops.py`
   - Contains current scanner inference, 3Shape/iTero heuristics, STL rename/classification.

4. **Template/destination decision responsibilities**
   - New:
     - `domain/decisions/template_selector.py`
     - `domain/decisions/destination_selector.py`
   - Wraps current decision order exactly.

5. **XML generation responsibilities**
   - New: `pipeline/xml_generation_pipeline.py`
   - Moves `generate_final_xml` and substitution logic without semantic edits.

6. **Packaging/copy/zip responsibilities**
   - New:
     - `pipeline/output_packaging_pipeline.py`
     - `infrastructure/fs/copy_ops.py`
     - `infrastructure/fs/archive_ops.py`
   - Includes materials/manufacturer copy, PDF copy, scan copy, zip/remove behavior.

7. **Failure handling responsibilities**
   - New: `pipeline/failure_pipeline.py`
   - Preserves failed-import marker file behavior and cleanup semantics.

8. **Compatibility wrapper**
   - Keep `case_processor_final_clean.py` exports (`process_case_from_id`, `process_case`) as wrappers during migration phases.

---

## 7. Config and Settings Consolidation Plan

### Current-state preservation
- Keep all existing keys, defaults, file names, and merge behavior.
- Keep frozen/non-frozen path behavior unchanged.
- Keep existing settings dialogs unchanged from user perspective.

### Consolidation approach
1. Introduce `infrastructure/config/settings_provider.py` as single read interface.
2. Move existing persistence implementations into:
   - `local_settings_store.py`
   - `admin_settings_store.py`
3. Build `runtime_config.py` as pure value assembly layer (no behavior changes).
4. Keep `config.py` as compatibility facade exporting the same names.
5. Update `evo_internal_client.py` to consume unified provider (preserve fallback semantics and values exactly).

### Packaging/frozen path preservation
- Maintain `_is_frozen_windows` logic.
- Maintain `%LOCALAPPDATA%\CaseCreator` behavior.
- Preserve runtime creation of output dirs (can be relocated internally but must behave identically).

---

## 8. UI Boundary Plan

### Must remain in UI
- Widget layout, threading ownership, and event-loop interactions.
- Settings dialog rendering and user interactions.
- Current queue management UX and timeout warnings.
- Existing log text display behavior (including panel split logic).

### Must move out of UI
- Any business-rule interpretation beyond display classification.
- Case processing orchestration internals.
- Config assembly logic (UI should consume service/provider APIs).

### Specific boundaries
1. **Log panel routing dependence**
   - Keep current exact-message contract by introducing a `log_routing_contract.py` module.
   - UI continues routing by current strings; backend message texts remain stable.

2. **Settings dialogs**
   - Keep in UI layer, but data payload validation and persistence calls go through service/provider boundary.

3. **Worker/threading behavior**
   - Keep `QThread`/worker pattern in UI layer.
   - Worker calls only stable service facade.

4. **Service boundaries**
   - `import_service` remains the UI-to-domain entrypoint.
   - UI never imports pipeline internals directly.

---

## 9. Legacy / Duplicate / Non-Authoritative Code Plan

### `import_gui.pyw`
- Classification: **legacy runtime fallback**
- Plan:
  - preserve behavior short-term,
  - isolate into legacy UI module,
  - keep compatibility entrypoint until decommission decision.

### `manual_import.py`
- Classification: **legacy/stale tooling**
- Plan:
  - move to tooling/legacy namespace,
  - mark explicitly non-authoritative,
  - exclude from primary runtime path.

### `Test scripts/*`
- Classification: **duplicate/non-authoritative mirrors**
- Plan:
  - isolate in tooling folder,
  - add explicit warning header,
  - forbid runtime imports from these files.

### Probe/test scripts (`evo_terminal_probe.py`, `rx_fetch_and_parse.py`, `test_evo_request.py`)
- Classification: **diagnostic tooling**
- Plan:
  - keep available, isolate under `tools/`,
  - not part of runtime packaging path unless explicitly required.

---

## 10. Safe Migration Phases

### Phase 0: Baseline lock
- Add behavior contract documentation and golden-log/test fixtures.
- No runtime code movement yet.
- Deliverable: baseline verification assets.

### Phase 1: Compatibility wrappers
- Introduce new folder scaffolding and wrapper modules only.
- Keep old files as authoritative implementations.
- Deliverable: no behavior change, imports still resolve old paths.

### Phase 2: Pure file extraction (no logic edits)
- Extract helper functions from `case_processor_final_clean.py` into new modules one family at a time.
- Keep old function signatures and call order via wrapper.
- Deliverable: smaller legacy file, same outputs/logs.

### Phase 3: Rule module centralization
- Move doctor/shade/material/template/destination/manual/naming predicates into `domain/rules/*`.
- Keep evaluator behavior and precedence identical.
- Deliverable: single rule location with unchanged runtime results.

### Phase 4: Pipeline assembly
- Build `import_pipeline.py` orchestrator mirroring current execution sequence exactly.
- Legacy entrypoint delegates to pipeline.
- Deliverable: functional parity with old processor.

### Phase 5: Config/provider unification
- Route config consumers through unified provider while preserving key names/defaults.
- Keep `config.py` compatibility exports.
- Deliverable: no UI/settings behavior change.

### Phase 6: UI boundary cleanup
- Move UI-adjacent internals into dedicated UI/service modules while preserving UX/log routing.
- Deliverable: cleaner UI code with same behavior.

### Phase 7: Legacy isolation and documentation
- Mark non-authoritative scripts and duplicates.
- Keep fallback entrypoints explicitly labeled.
- Deliverable: reduced accidental-edit risk.

---

## 11. Risk Register

1. **Template precedence drift**
   - Risk: changing branch order in extracted rules.
   - Mitigation: golden decision-path tests for representative case matrix.

2. **Doctor override inconsistency**
   - Risk: accidentally unifying strict/loose Serbia checks and changing behavior.
   - Mitigation: preserve both semantics until explicit behavior-change phase.

3. **Scanner heuristic regressions**
   - Risk: folder selection or STL classification changes.
   - Mitigation: fixture-based scanner test corpus (3Shape, iTero, Sirona edge names).

4. **Destination/path changes**
   - Risk: AI or Argen routing drift through refactor.
   - Mitigation: snapshot output destination assertions per template family.

5. **Log compatibility breakage**
   - Risk: minor wording changes break PySide6 panel routing.
   - Mitigation: lock and assert exact log strings used for routing.

6. **Config source divergence**
   - Risk: client modules using different config sources.
   - Mitigation: centralized provider and compatibility facade tests.

7. **Packaging regressions**
   - Risk: moved modules break frozen resource paths.
   - Mitigation: keep entrypoint/resource wrappers and run packaged smoke checks each phase.

8. **Editing wrong duplicate files**
   - Risk: changes applied to `Test scripts/*` copies.
   - Mitigation: isolate and label non-authoritative folders early.

---

## 12. Validation Strategy

### A. Regression fixture matrix
- Build a deterministic set of case fixtures spanning:
  - signature/non-signature doctors,
  - Abby/Dew + Brier Creek scenarios,
  - C3/A4 and normal shades,
  - study/no-study,
  - iTero/3Shape/non-3Shape paths,
  - anterior/posterior,
  - modeless flags and material variants.

### B. Decision-path verification
- For each fixture, assert unchanged:
  - selected template path,
  - destination root,
  - manual-review outcome,
  - case suffix,
  - zip/non-zip decision.

### C. Output artifact verification
- Compare before/after:
  - output folder/zip location,
  - generated XML placeholder substitutions,
  - Materials shade injection behavior,
  - scan copy naming structure.

### D. Scanner-case verification
- Run controlled folder-structure tests validating:
  - 3Shape patient folder selection rules,
  - iTero nested folder scoring,
  - STL keyword classification and fallback.

### E. Log compatibility verification
- Capture full log streams and assert exact text for routing-critical lines.
- Confirm PySide6 summary/process panel routing outcome is unchanged.

### F. Settings/config verification
- Assert local/admin settings read/write behavior unchanged.
- Assert frozen/non-frozen settings location behavior unchanged.

### G. Packaging verification
- Smoke-test source launch and one-folder packaged launch.
- Validate required assets and settings persistence behavior.

---

## 13. First Execution Pass Recommendation

Safest first code-change pass:

1. Create new module scaffolding (`domain`, `pipeline`, `infrastructure`, `app/ui`, `compat`) with no logic moved yet.
2. Introduce compatibility wrappers only:
   - keep existing entrypoints (`pyside6_ui.py`, `import_service.py`, `config.py`, `case_processor_final_clean.py`) as authoritative.
   - wrappers can import old implementations and re-export unchanged symbols.
3. Add non-runtime classification headers for legacy/duplicate/tooling files (no behavior effect).
4. Add minimal automated parity checks for:
   - template selection outputs,
   - destination outputs,
   - manual gate outcomes,
   - critical log text lines.

This pass is low-risk because it creates architecture seams first, before moving any logic.

