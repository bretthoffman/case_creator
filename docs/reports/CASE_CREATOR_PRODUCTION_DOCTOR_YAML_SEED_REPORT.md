# CASE CREATOR PRODUCTION DOCTOR YAML SEED REPORT

## 1. Summary of changes

- **`business_rules/v1/doctor_overrides.yaml`** now includes production-ready **Abby Dew** and **VD Brier Creek** multi-outcome rules (`abby_dew_multi_outcome`, `vd_brier_creek_multi_outcome`), copied from the validated offline parity fixture with clearer comments and rule IDs.
- Header documentation explains **simple** vs **richer** rules, **`CASE_CREATOR_DOCTOR_OUTCOMES_LIVE`** gating, observability, and cautions against casual edits.
- **`tests/doctor_policy_parity_harness.py`** gains **`_production_yaml_seed_rows()`**: validates production YAML, checks rule ids and outcome counts vs the offline fixture, asserts **no override** for Abby when the flag is off and `business_rules/v1` is loaded, and asserts **parity** with the offline resolver for four cases when the flag is on.
- **`tests/fixtures/doctor_policy_abby_vd_offline.yaml`** header updated to note parity with production shapes.

No changes to `template_utils`, other config families, or default flag behavior in `config.py`.

## 2. Files modified

| File | Change |
|------|--------|
| `business_rules/v1/doctor_overrides.yaml` | Seeded Abby/VD `outcomes[]` rules + comments; kept disabled simple example rule. |
| `tests/doctor_policy_parity_harness.py` | Production seed validation rows. |
| `tests/fixtures/doctor_policy_abby_vd_offline.yaml` | Comment alignment with production. |
| `CASE_CREATOR_PRODUCTION_DOCTOR_YAML_SEED_REPORT.md` | This report (new). |

## 3. Seeded production rules

- **`abby_dew_multi_outcome`:** `predicate: abby_dew`, shared top-level `when` (no study/signature/anterior, `excludes_modeless_hint_route`), **10** conditional `outcomes` matching material, `shade_usable`, scanner, and non-Argen shade — same structure as the offline fixture.
- **`vd_brier_creek_multi_outcome`:** `predicate: vd_brier_creek`, same top-level `when`, **4** `outcomes` for iTero/non–iTero and non-Argen shade branches — same as offline.
- **`example_single_key_doctor`:** unchanged, **disabled** simple-rule example.

## 4. Safety posture

- **`CASE_CREATOR_DOCTOR_OUTCOMES_LIVE`** remains **default off** (`config.doctor_outcomes_live_enabled()`).
- When the flag is off, `resolve_doctor_policy` **skips** rules that only define `outcomes[]`, so the new Abby/VD blocks **do not** return a template key and **do not** change production template selection.
- Inline **`template_utils.select_template`** Abby/VD branches are unchanged and remain authoritative whenever no override key is returned.

## 5. Validation performed

- `python3 tests/doctor_policy_parity_harness.py` — exit **0**, including **8** `production_seed` rows (schema validation, ids, outcome counts, flag-off Abby on repo path, flag-on parity vs offline fixture for four case shapes).
- Import smoke: `from domain.decisions.template_selector import select_template_path` succeeds.
- **Shade / routing / argen / other YAML families:** not edited in this pass.

## 6. Risks or limitations

- Enabling **outcomes live** in production will allow YAML to **override** `select_template` when outcomes match — pilot with logging (`case_creator_doctor_outcomes_override`) and monitoring.
- **VD + iTero + Argen-usable shade** gaps in `template_utils` (documented in the final parity report) remain; YAML does not fix undefined template branches.
- Drift risk if **`template_utils`** or **`doctor_when_eval`** changes without updating YAML and harness.

## 7. Recommended next pass

1. **Controlled pilot:** Set `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` only in staging or a narrow production cohort; review override logs.
2. **Template gaps:** Define or reject VD edge cases in `template_utils` so code and YAML agree on all live combinations.
3. **Later cleanup:** Only after sustained correct flagged behavior, consider reducing duplication between code and YAML (separate explicit pass).

---

## Final chat summary

1. **Richer Abby/VD rules** are now in **`business_rules/v1/doctor_overrides.yaml`** with production-oriented ids and documentation.
2. **Baseline behavior** is **unchanged by default** because multi-outcome rules are **ignored** until the env flag is set.
3. The system is **ready for controlled flagged trial** (same mechanism as before, now backed by production-seeded YAML validated in the harness).
4. **Safest next pass:** Pilot with the flag on in a limited environment, watch observability lines, then address template edge cases before any code deletion.
