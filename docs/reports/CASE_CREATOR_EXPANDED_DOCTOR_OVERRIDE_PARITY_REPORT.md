# CASE CREATOR EXPANDED DOCTOR OVERRIDE PARITY REPORT

## 1. Summary of changes

This pass **expanded doctor override validation** to support bounded **`match.predicate`**, rule-level **`when`**, and ordered **`outcomes`** (each with its own `when` + `template_override_key` action). It added a **pure offline resolver** (`domain/decisions/doctor_policy_resolver.py`) plus shared **`when`** evaluation (`domain/decisions/doctor_when_eval.py`), a **runnable parity harness** (`tests/doctor_policy_parity_harness.py`), and an **offline-only YAML fixture** (`tests/fixtures/doctor_policy_abby_vd_offline.yaml`).

**Production template selection is unchanged:** `template_utils.select_template` still owns Abby/VD branching. **Multi-outcome rules are ignored by the live doctor runtime** so richer YAML cannot alter behavior until a future cutover.

## 2. Files modified

| File | Change |
|------|--------|
| `infrastructure/config/business_rule_schemas.py` | Expanded `validate_doctor_overrides` + helpers for `when` / `outcomes` / `predicate`. |
| `infrastructure/config/doctor_override_runtime.py` | Predicate match; skip rules with `outcomes`; optional rule-level `when` when `case_data` passed; signature extended. |
| `domain/decisions/template_selector.py` | Passes `case_data` into `resolve_doctor_template_override_key` (enables future/simple `when` without changing current shipped YAML). |
| `domain/decisions/doctor_when_eval.py` | **New** — bounded clause/group evaluation. |
| `domain/decisions/doctor_policy_resolver.py` | **New** — offline policy → optional template key. |
| `tests/fixtures/doctor_policy_abby_vd_offline.yaml` | **New** — offline Abby/VD multi-outcome fixture. |
| `tests/doctor_policy_parity_harness.py` | **New** — parity runner + simple live override smoke. |
| `business_rules/v1/doctor_overrides.yaml` | Comment pointer to offline fixture only. |
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_PARITY_REPORT.md` | This report. |

## 3. Schema expansion

Doctor rules now support:

| Feature | Details |
|---------|---------|
| `match.predicate` | Optional. Allowed: `abby_dew`, `vd_brier_creek` (must match `domain/rules/doctor_rules.py` semantics). |
| `match.contains_any` / `contains_all` | Optional when `predicate` is set; both may be combined (both must pass). If `predicate` is absent, at least one of contains lists is still required. |
| Rule-level `when` | Optional. Exactly one of `all` or `any`, non-empty clause list. |
| `outcomes` | Optional ordered list of `{ when, action }`. Each `action` may only include `template_override_key` (no label keys in outcomes in this pass). |
| Clause forms | `{"field": "<has_study\|signature\|shade_usable\|is_anterior>", "eq": bool}` OR singleton boolean maps: `material_is_adz`, `scanner_is_itero`, `non_argen_shade`. |

**Mutual exclusion:** If `outcomes` is non-empty, `action` must be empty. Simple rules keep a non-empty `action` and no `outcomes`.

**Not added (by design):** label rules, destination overrides in outcomes, arbitrary DSL, raw paths.

## 4. Offline resolver design

- **Module:** `domain/decisions/doctor_policy_resolver.py`
- **Entry:** `resolve_doctor_policy_template_key(case_data, doctor_cfg) -> Optional[str]`
- **Behavior:** Walks enabled rules in order; matches doctor via `predicate` and/or substring lists; evaluates rule `when` then first matching outcome `when`; returns `template_override_key` string or `None`.
- **Dependencies:** `domain` only (no infrastructure imports).

## 5. Parity harness coverage

Run: `python tests/doctor_policy_parity_harness.py`

| Scenario | Intent |
|----------|--------|
| Abby + Adz + explicit slice (non‑iTero, Argen-usable shade) | Mirrors `select_template` Abby → `ai_adzir`. |
| Abby + Envision + same slice | Abby → `ai_envision`. |
| VD Brier + Adz + non‑iTero | VD → `ai_adzir_model`. |
| VD Brier + Envision + non‑iTero | VD → `ai_envision_model`. |
| Abby + iTero + non‑Argen shade (C3) | Earlier `elif` branch → `ai_adzir`; fixture includes a more specific outcome row. |
| Temp dir simple `contains_all` rule | Proves live `resolve_doctor_template_override_key` still applies simple overrides. |
| Repo `business_rules/v1` load | Ensures shipped `doctor_overrides.yaml` still validates. |

## 6. Parity results

For the **offline fixture** in `tests/fixtures/doctor_policy_abby_vd_offline.yaml`, the resolver **matches** `template_utils.select_template` for all harness scenarios above (including the Abby + non‑Argen shade + iTero branch after adding a dedicated outcome).

**Caveat:** Full cartesian parity over the entire `select_template` `elif` chain is **not** claimed—only the Abby/VD-focused slices exercised here. Additional outcomes rows would be needed for exhaustive coverage before a live cutover.

## 7. Production safety

- **`template_utils.select_template`** — untouched.
- **Live doctor runtime** — **`continue` when `rule.get("outcomes")` is truthy**, so multi-outcome YAML in production would be **ignored** until intentionally enabled in code.
- **Shipped `doctor_overrides.yaml`** — still only **disabled** simple example + comments; no enabled multi-outcome rules.
- **Offline fixture** — lives under `tests/fixtures/`; app does not load it unless `CASE_CREATOR_BUSINESS_RULES_DIR` points there.
- **`template_selector`** — still calls `select_template` first; override only applies when live resolver returns a key (same as before for current YAML).
- **Serbia / route labels** — not driven by the new resolver in this pass.

## 8. Risks or limitations

- **Silent ignore:** If an operator places enabled **`outcomes`** rules in production YAML expecting them to work, **they will not apply** until cutover—documented here and via comments in repo YAML.
- **`when` on simple rules:** Evaluated only when `case_data` is passed (now done from `template_selector`). Callers passing only `doctor_name` elsewhere would skip `when` (backward compatible).
- **Label / Serbia breadth vs VD narrow template** — still separate predicates in code; not modeled in doctor YAML in this pass.
- **Exhaustive parity** — more branches (signature, study, anterior, modeless, etc.) need additional harness cases before deleting inline Abby/VD code.

## 9. Recommended next pass

1. Expand the parity harness with more **grid cases** (study, anterior, modeless, signature doctor).
2. Add an **opt-in feature flag** (e.g. env or config) to allow **`outcomes`** evaluation in live `resolve_doctor_template_override_key` / `select_template_path`, default **off**.
3. When flag on and parity suite is green, **remove** redundant `is_abby` / `is_vd_serbia` branches from `select_template` in a dedicated pass.

---

## Final chat summary

1. **Richer schema support:** `predicate`, rule `when`, ordered `outcomes` with bounded `when` clauses and `template_override_key` actions; strict validation; outcome actions **exclude** label keys.
2. **Abby/VD offline parity:** Achieved for the harness scenarios (including Abby + non‑Argen shade + iTero) against `tests/fixtures/doctor_policy_abby_vd_offline.yaml`.
3. **Not live yet:** Multi-outcome rules are **skipped** in `doctor_override_runtime`; `doctor_policy_resolver` is **offline-only**; Serbia label behavior unchanged.
4. **Safest next pass:** Broaden parity grid + introduce a **default-off flag** for live `outcomes` before any template engine deletion.
