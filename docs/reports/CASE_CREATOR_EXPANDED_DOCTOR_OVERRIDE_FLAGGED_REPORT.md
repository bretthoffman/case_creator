# CASE CREATOR EXPANDED DOCTOR OVERRIDE FLAGGED REPORT

## 1. Summary of changes

- **Parity harness:** Expanded offline Abby Dew / VD Brier Creek scenarios: modeless hint route (Abby and VD) with expected **no policy** (code-owned `argen_modeless_*` path), four **shade_usable false** Abby rows (iTero and non–iTero × ADZ and Envision), and retained study / anterior / signature abstention cases plus existing material / scanner / non-Argen shade slices.
- **Feature flag:** `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` (default off; truthy only for `1` / `true` / `yes` / `on`) gates evaluation of doctor rules that define `outcomes[]` in `resolve_doctor_template_override_key`. Simple `action`-only rules are unchanged.
- **Bounded `when` clause:** `excludes_modeless_hint_route: true` uses the same effective Argen hint route as `template_utils` (`normalized_hint_route` + `effective_argen_hint_route`) so multi-outcome parity rules **abstain** on the modeless fast path instead of incorrectly returning `ai_*` templates.
- **No** removal of inline Abby/VD logic in `template_utils.select_template`, **no** label/Serbia routing through the doctor resolver, **no** change to shipped `business_rules/v1` doctor rules beyond schema allowing the new clause for future/parity YAML.

## 2. Files modified

| File | Change |
|------|--------|
| `config.py` | `doctor_outcomes_live_enabled()` (existing): env gate for live `outcomes[]`. |
| `domain/decisions/doctor_policy_resolver.py` | Docstring: documents live wiring and `allow_outcomes` gate. |
| `domain/decisions/doctor_when_eval.py` | `excludes_modeless_hint_route` clause; shared effective hint route helper. |
| `infrastructure/config/business_rule_schemas.py` | Validate `excludes_modeless_hint_route` (must be `true`). |
| `infrastructure/config/doctor_override_runtime.py` | (Prior pass) Delegates to resolver with `allow_outcomes=doctor_outcomes_live_enabled()`. |
| `tests/fixtures/doctor_policy_abby_vd_offline.yaml` | Modeless abstention + Abby `shade_usable: false` outcomes. |
| `tests/doctor_policy_parity_harness.py` | Additional parity rows; flag/simple/repo checks unchanged in intent. |
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_FLAGGED_REPORT.md` | This report (new). |

## 3. Feature flag behavior

| State | Behavior |
|-------|----------|
| **Off** (unset, empty, or not truthy) | `resolve_doctor_policy_template_key(..., allow_outcomes=False)` skips any rule that defines `outcomes`. Simple rules (`match` + `when` + `action.template_override_key` only) still apply. Matches pre-flag production: multi-outcome YAML did not affect live template overrides. |
| **On** (`CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` ∈ {`1`,`true`,`yes`,`on`}) | Rules with `outcomes[]` are evaluated after doctor match and rule-level `when`. First matching outcome’s `template_override_key` wins. |

**Precedence (no double-application bug):** `domain/decisions/template_selector.select_template_path` still calls `template_utils.select_template` first, then **replaces** the path only if `resolve_doctor_template_override_key` returns a key. With the flag off, multi-outcome rules never return a key, so behavior matches the previous live seam. With the flag on, YAML may override the folder chosen by `select_template` when an outcome matches—intentional for experimentation; inline Abby/VD branches are not deleted.

## 4. Parity harness expansion

Offline fixture `tests/fixtures/doctor_policy_abby_vd_offline.yaml` vs `select_template` / `resolve_doctor_policy_template_key(..., allow_outcomes=True)`:

- **Match:** Explicit ADZ / Envision Argen hints; non-Argen shade + iTero; VD model vs non-model + iTero non-Argen; Abby `shade_usable` false (four combinations).
- **No policy (rule abstains):** Anterior; `has_study`; VD `has_study`; **modeless** hint (Abby and VD)—policy must be `None` while authoritative template is `argen_modeless_*`.
- **Note:** `abby_signature_itero_adz` still expects **no policy** (fixture top `when` requires `signature: false`); authoritative template may be `ai_adzir` from code-owned signature branch—parity is “resolver abstains,” not “folder equals policy.”

Harness also checks: flag off/on, simple `contains_all` override with flag off/on, and loading `business_rules/v1`.

## 5. Validation performed

- `python3 tests/doctor_policy_parity_harness.py` — exit 0; all parity, flag, simple override, and repo load checks passed.
- Import smoke: `doctor_outcomes_live_enabled()` defaults false; `doctor_policy_resolver` and `doctor_override_runtime` import cleanly.
- **Not** run: full pytest suite (if present); **not** exercised: every `argen_modes` combination against multi-outcome YAML.

## 6. Production safety

- Default **flag off** → `outcomes[]` ignored in live runtime → same as before multi-outcome live wiring.
- Shipped **`business_rules/v1/doctor_overrides.yaml`** unchanged by this pass; new schema clause is additive.
- **Serbia / label** behavior is untouched; no label keys in doctor outcomes schema.
- Inline **Abby/VD** template branches remain in `template_utils.py`.

## 7. Risks or limitations

- **Cutover readiness:** Parity is broader (modeless, shade_usable, study, anterior, signature abstention, material/scanner/shade grid) but **not** exhaustive over branch order edge cases, all `argen_modes` modes, or every signature/study crossover.
- **Flag on:** Outcomes can **override** `select_template`’s folder when they match; operators must treat this as experimental until parity and monitoring justify cutover.
- **`excludes_modeless_hint_route`:** Config authors must add it to multi-outcome Abby/VD-style rules that should not compete with the modeless fast path; omission could reintroduce wrong overrides for modeless cases when the flag is on.

## 8. Recommended next pass

1. Add a small set of **argen_modes** parity rows (e.g. `always_with_contact_models` / `always_without_contact_models`) against the same offline fixture, if those modes are enabled in target environments.
2. Extend **VD** multi-outcome coverage for any **shade_usable**-sensitive branches that matter in production (if distinct from Abby).
3. Operational: metrics or logging when `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` is on and an outcome overrides `select_template`.
4. When parity is sufficient: optional **cutover** pass (separate from this readiness work) to reduce duplication between YAML and code—**not** required for this flag-only pass.

---

## Final chat summary

1. **Richer doctor behavior behind the flag:** With `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` enabled, validated `outcomes[]` rules can return `template_override_key` in the live doctor override seam, replacing the path from `select_template` when they match.
2. **Baseline default:** With the flag off (default), multi-outcome rules are skipped; simple doctor overrides and all non-doctor config families behave as before this pass.
3. **Cutover confidence:** **Not yet** strong enough for unconditional removal of code-owned Abby/VD branches—parity is meaningfully wider but not full branch enumeration.
4. **Safest next pass:** Add **argen_modes**-aware parity cases and optional observability when outcomes live is on; then reassess cutover.
