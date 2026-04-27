# CASE CREATOR EXPANDED DOCTOR OVERRIDE ARGEN PARITY REPORT

## 1. Summary of changes

- **Argen modes parity:** The doctor policy harness now runs Abby Dew and VD Brier Creek scenarios under temporary `business_rules` dirs that set `argen_modes.contact_model_mode` to `legacy_default`, `always_with_contact_models`, and `always_without_contact_models`. Authoritative template folders come from `template_utils.select_template`, and policy from the offline Abby/VD multi-outcome fixture, both evaluated **inside the same config context** so `effective_argen_hint_route` matches between code and `excludes_modeless_hint_route` in YAML.
- **Observability:** `select_template_path` logs a single structured `info` line when `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` is on, the winning rule source is **`outcomes`**, and the override template folder differs from the baseline folder from `select_template`. Simple `action`-only rules do not emit this line. With the flag off, no new log path runs for this event.
- **Resolver metadata:** `resolve_doctor_policy` / `DoctorPolicyResult` expose `template_key` plus `source` (`outcomes` | `simple` | `None`). Live entry `resolve_doctor_template_override_with_source` supports the seam without changing override keys.

## 2. Files modified

| File | Change |
|------|--------|
| `domain/decisions/doctor_policy_resolver.py` | `resolve_doctor_policy`, `DoctorPolicyResult`, `DoctorPolicySource`; `resolve_doctor_policy_template_key` delegates. |
| `infrastructure/config/doctor_override_runtime.py` | `resolve_doctor_template_override_with_source`; existing override function unchanged semantically. |
| `domain/decisions/template_selector.py` | Logging for outcomes-based override vs baseline; uses `with_source` resolution. |
| `tests/doctor_policy_parity_harness.py` | `_argen_parity_rows`, `_observability_rows`, shared temp rules-dir helper, summary lines. |
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_ARGEN_PARITY_REPORT.md` | This report (new). |

## 3. Parity expansion

New group **`parity_argen_modes`** (temp `argen_modes.yaml` only; policy still loaded from `tests/fixtures/doctor_policy_abby_vd_offline.yaml`):

| Scenario | `contact_model_mode` | Expectation |
|----------|----------------------|-------------|
| Abby ADZ with `argen_adzir` hint | `always_with_contact_models` | Authoritative `argen_modeless_adzir`; policy **abstains** (`None`) — modeless fast path; fixture excludes modeless effective route. |
| VD ADZ, same | `always_with_contact_models` | Same. |
| Abby / VD with **raw** `modeless` hint + ADZ | `always_without_contact_models` | Effective route becomes `argen_adzir`; authoritative **AI** folders; policy **matches** fixture outcomes. |
| Abby modeless hint + ADZ | `legacy_default` | Authoritative `argen_modeless_adzir`; policy **abstains** (control for explicit legacy file). |

**Harness lesson:** Policy rows that depend on `effective_argen_hint_route` must be computed under the **same** `CASE_CREATOR_BUSINESS_RULES_DIR` (and cache clears) as `select_template`, or parity will falsely diverge.

## 4. Observability behavior

- **Logger:** `domain.decisions.template_selector` (`logging.getLogger(__name__)`).
- **Message prefix:** `case_creator_doctor_outcomes_override`
- **Fields:** `doctor`, `baseline_template`, `override_template` (template folder keys, not filesystem paths).
- **Conditions (all required):** `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` truthy; resolution source `outcomes`; override key non-empty; override folder **≠** baseline folder.
- **Not emitted:** Flag off; simple-rule overrides; outcomes that agree with baseline; unrelated template selection.

## 5. Validation performed

- `python3 tests/doctor_policy_parity_harness.py` — exit 0: offline parity, **argen_modes** parity, observability (flag off / flag on / simple override silent), flag rows, simple override rows, repo `business_rules/v1` load.
- Import smoke: `select_template_path`, `resolve_doctor_template_override_with_source`, `resolve_doctor_policy` resolve without circular import errors in exercised paths.

## 6. Production safety

- **`CASE_CREATOR_DOCTOR_OUTCOMES_LIVE`** default remains off; multi-outcome rules still skipped in live resolution when off.
- **Logging:** The new `info` call is guarded by the flag and by `source == "outcomes"` and by a real template change, so baseline deployments see **no** extra noise from this path.
- **Functional:** Override keys are unchanged; only the resolution path returns an extra tuple internally for the template selector.

## 7. Risks or limitations

- **Cutover:** Arg parity covers the three shipped modes for the most material Abby/VD × hint-route interactions; it does not exhaust combinatorics (e.g. every envision/modeless/argen_modes triple, AI flags, or full signature/study grid under each mode).
- **Logging:** If root log level suppresses `INFO`, the line may not appear unless logging config is adjusted — by design, non-functional.
- **Config consistency:** Live deployments must keep `argen_modes` and doctor `when` clauses aligned (as in the offline fixture) to avoid surprises when outcomes go live.

## 8. Recommended next pass

1. Optional **structured** log field (e.g. rule id) once YAML exposes stable rule identifiers in the resolver result — keep bounded; no PII beyond doctor display name already logged elsewhere in template flow.
2. Broader **matrix** under `always_with_contact_models` for **envision** hints if production uses that combination heavily.
3. Cutover planning only after sustained outcomes-live trial and parity expansion — **do not** remove code-owned Abby/VD branches in the next pass without that evidence.

---

## Final chat summary

1. **New argen_modes-aware parity:** Five harness rows exercise `always_with_contact_models` (Abby/VD `argen_adzir` → modeless authoritative + policy abstention), `always_without_contact_models` (raw modeless hint → effective `argen_adzir` + policy match), and `legacy_default` modeless control.
2. **Observability:** One `INFO` log line when the flag is on and an **`outcomes[]`** rule changes the template folder away from `select_template`; simple overrides and flag-off runs do not emit it.
3. **Baseline default:** Unchanged when the flag is off; no new logging on that path for these events.
4. **Cutover:** Closer in the sense that argen_modes and outcomes-live interactions are now regression-tested, but **still not** a full safe cutover: coverage remains bounded and code-owned branches remain required.
