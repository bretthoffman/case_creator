# CASE CREATOR ROUTE LABEL OVERRIDE REPORT

## 1. Summary of changes

This pass made doctor YAML `route_label_override_key` **live** for route/readback behavior while keeping destination routing unchanged.

Implemented:

- Bounded schema support already present was kept strict (allowed label enums only).
- Runtime now reads doctor label override and applies it at destination selection seam.
- Destination key flow (`argen` vs `1_9`) remains template/family-driven.
- Route label override is applied only when compatible with template family label types.

Result: YAML can now express Serbia-style readback behavior (label) independently from the destination routing target.

## 2. Files modified

- `domain/decisions/doctor_policy_resolver.py`
- `infrastructure/config/doctor_override_runtime.py`
- `domain/decisions/destination_selector.py`
- `case_processor_final_clean.py`
- `tests/test_unified_business_rules_config.py`
- `tests/test_route_label_override_runtime.py` (new)
- `business_rules/v1/README.md`
- `CASE_CREATOR_ROUTE_LABEL_OVERRIDE_REPORT.md` (this file)

## 3. Current behavior audit findings

Before this pass:

- Destination selection came from `resolve_destination_key(...)`.
- Route/readback label came from `routing_rules.route_label_for_template(template, doctor)`.
- Serbia readback behavior was produced by built-in doctor-name heuristics (`brier creek`) in `routing_rules.is_serbia_case`, not by live YAML label override.
- `route_label_override_key` existed in schema validation but was not applied in live routing seam.

## 4. Schema changes

No broad schema redesign was required.

- `doctor_overrides.rules[].action.route_label_override_key` remains supported and strictly validated.
- Allowed values remain bounded to known runtime labels:
  - `argen`
  - `designer`
  - `serbia`
  - `ai_designer`
  - `ai_serbia`
- Unknown values are rejected (test coverage added).

## 5. Runtime mapping

Runtime flow now:

1. `resolve_destination_key(template)` decides real destination (`argen` or `1_9`) exactly as before.
2. Baseline label still starts from `routing_rules.route_label_for_template(...)`.
3. Doctor YAML override is resolved via `resolve_doctor_route_label_override_key(...)`.
4. Override is applied only if label is compatible with template family:
   - argen templates -> `argen`
   - study/anterior templates -> `designer` / `serbia`
   - ai templates -> `ai_designer` / `ai_serbia`

This keeps label routing distinct from destination routing and avoids impossible label/template combinations.

## 6. Validation performed

- Imports and integration compiled via test run.
- No circular import failures observed.
- Schema validation checks:
  - allowed `route_label_override_key` accepted
  - unknown label rejected
- Runtime checks:
  - destination remains `1_9` while label becomes `serbia` with YAML override
  - baseline VD/Brier-Creek Serbia behavior still works without YAML override
- Regression suite run:
  - `python3 -m unittest tests.test_route_label_override_runtime tests.test_unified_business_rules_config tests.test_unified_retirement_equivalence tests.test_business_rule_loader_dual_read -v`
  - all tests passed.

## 7. Risks or limitations

- Label overrides currently flow from simple doctor actions (schema outcomes actions remain template-only).
- Overriding to incompatible label families is intentionally ignored at runtime compatibility guard.
- This pass does not introduce a separate top-level label family; behavior remains doctor-rule driven.

## 8. Recommended next pass

Safest next step:

- Add optional observability/debug log line when a compatible doctor label override is applied (and when an incompatible override is ignored), behind existing debug logging patterns.
- Optionally add one seeded disabled example rule in `case_creator_rules.yaml` showing label-only override usage for operators.
