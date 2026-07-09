# CASE CREATOR ITERO OUTSOURCE TEMPLATE REROUTE REPORT

## 1. Summary of changes

Outsource iTero cases that previously selected `itero_*` study/anterior templates or `ai_adzir`/`ai_envision` now use the same template families as non-iTero outsource (`reg_*` study/anterior and `ai_*_model` posteriors). Designer iTero cases are unchanged.

The reroute is applied in `select_template_path()` (the production entry point used by `case_processor_final_clean.py`) after baseline template selection and any doctor override, using the existing `resolve_delivery_mode()` decision.

EMax iTero outsource cases were already routed to `reg_emax_*` templates by the baseline ladder (no `itero_emax_*` family exists); no code change was required for emax, but tests confirm the behavior is preserved.

## 2. Files modified

| File | Change |
|------|--------|
| `domain/rules/template_rules.py` | Added `ITERO_OUTSOURCE_FOLDER_MAP` and `remap_itero_folder_for_outsource()` (study/anterior + posterior ai_* reroutes) |
| `domain/decisions/template_selector.py` | Added `_apply_itero_outsource_template_reroute()`; called at end of `select_template_path()` |
| `tests/test_itero_outsource_template_reroute.py` | New focused test module (8 cases) |
| `CASE_CREATOR_ITERO_OUTSOURCE_TEMPLATE_REROUTE_REPORT.md` | This report |

## 3. Root cause

Template selection (`template_utils.select_template`) chooses `itero_*` vs `reg_*` study/anterior templates based solely on scanner type (`is_itero_scanner`). Delivery mode (outsource vs designer) was intentionally decoupled and resolved later in `process_case()`.

For the new outsource/designer delivery model, `itero_*` templates use `ScanItRestoration` (digital impression, models off). Outsource iTero workflows need the `reg_*` templates, which have the digital impression / antagonist settings configured correctly for outsource. Designer iTero cases should keep the existing `itero_*` behavior.

## 4. Fix applied

A post-selection reroute in `select_template_path()`:

1. Resolve delivery mode via `resolve_delivery_mode(case_data)`.
2. If mode is **outsource** and scanner is **iTero**, remap the selected folder through `remap_itero_folder_for_outsource()`.
3. If the folder is in the remap map (`itero_*` study/anterior or `ai_adzir`/`ai_envision`), rebuild the path using the corresponding outsource equivalent.
4. Otherwise return the path unchanged.

`template_utils.select_template()` is unchanged so internal parity harnesses and the baseline ladder remain stable; only the production wrapper applies the reroute.

## 5. Exact template remapping behavior

Applied **only when** `resolve_delivery_mode(case_data) == "outsource"` **and** scanner contains `"itero"` (case-insensitive):

| Baseline (would have selected) | Rerouted to |
|----------------------------------|-------------|
| `itero_adzir_anterior` | `reg_adzir_anterior` |
| `itero_adzir_study` | `reg_adzir_study` |
| `itero_envision_anterior` | `reg_envision_anterior` |
| `itero_envision_study` | `reg_envision_study` |
| `ai_adzir` | `ai_adzir_model` |
| `ai_envision` | `ai_envision_model` |

**Not remapped:**

- Designer delivery (doctor in `delivery_modes.designer_doctor_names` or shade in `shade_overrides.non_argen_shade_markers`, e.g. C3/A4)
- Non-iTero scanners
- `ai_*`, `reg_emax_*`, and all other template families
- Folders not in the map above (no-op)

**EMax:** Baseline already selects `reg_emax_ant`, `reg_emax_post`, `reg_emax_ant_study`, or `reg_emax_post_study` regardless of scanner; reroute is a no-op.

## 6. Validation/tests performed

```bash
python3 -m unittest tests.test_itero_outsource_template_reroute -v
python3 -m unittest tests.test_template_argen_reroute tests.test_baseline_delivery_isolation tests.test_emax_routing -v
```

`tests/test_itero_outsource_template_reroute.py` covers:

- iTero + outsource + adzir anterior → `reg_adzir_anterior`
- iTero + outsource + adzir study → `reg_adzir_study`
- iTero + outsource + envision anterior → `reg_envision_anterior`
- iTero + outsource + envision study → `reg_envision_study`
- iTero + designer (C3 shade) → `itero_envision_study` (unchanged)
- iTero + designer doctor → `itero_adzir_anterior` (unchanged)
- iTero + outsource + envision posterior → `ai_envision_model` (matches trios)
- iTero + outsource + adzir posterior → `ai_adzir_model`
- iTero + designer posterior (C3 shade) → `ai_envision` (unchanged)
- Non-iTero + outsource + study → `reg_envision_study` (unchanged)

All 44 tests in the combined template/delivery/emax suite passed.

## 7. Remaining risks or limitations

- **Direct `select_template()` callers** (e.g. `doctor_policy_parity_harness._folder_from_select`) still see the pre-reroute `itero_*` folders. Production uses `select_template_path()` only; parity harness authoritative column is intentionally the raw ladder output.
- **Doctor YAML template overrides** to an `itero_*` study/anterior key on an outsource iTero case will also be rerouted to `reg_*`. This is consistent with the outsource workflow goal; if a future override must force `itero_*` for outsource, an explicit exemption would be needed.
- **`ai_*` outsource templates** — outsource iTero posteriors now use `ai_*_model` like trios; designer iTero posteriors still use `ai_*`.

## 8. Recommended next step

Smoke-test one real outsource iTero study case and one designer iTero study case (C3 shade or designer doctor) through `process_case()` on a staging machine, confirming XML uses `ModelBuilder`/antagonist settings for outsource and `ScanItRestoration` for designer. Then tag/build/push per normal release workflow.
