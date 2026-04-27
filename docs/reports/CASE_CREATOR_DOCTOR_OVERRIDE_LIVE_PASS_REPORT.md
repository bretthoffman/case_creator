CASE CREATOR DOCTOR OVERRIDE LIVE PASS REPORT

## 1. Summary of changes

This pass made **doctor override config** live in a narrow, controlled way:
- live source: validated `doctor_overrides.json` via existing business-rule loader foundation.
- live action enabled: `template_override_key` only.
- integration seam: template decision shell (`domain/decisions/template_selector.py`).

All other business-rule config families remain read-only preview only.

## 2. Files modified

Created:
- `infrastructure/config/doctor_override_runtime.py`
- `CASE_CREATOR_DOCTOR_OVERRIDE_LIVE_PASS_REPORT.md`

Modified:
- `infrastructure/config/business_rule_loader.py` (added optional env discovery override)
- `domain/decisions/template_selector.py` (applies doctor template override safely)

## 3. Live integration point

Runtime flow for doctor overrides in this pass:

1. `template_selector.select_template_path(case_data)` computes baseline template via existing authoritative engine (`template_utils.select_template(...)`).
2. It then calls `resolve_doctor_template_override_key(doctor_name)` from `infrastructure/config/doctor_override_runtime.py`.
3. That runtime helper reads validated effective config from `load_business_rule_config_preview()`, checks enabled doctor rules in deterministic file order, and returns only `template_override_key` when a rule matches.
4. If a valid override key is returned, selector maps it to template path via `template_rules.build_template_path(...)`.
5. Otherwise baseline template is returned unchanged.

Safety behavior:
- any loader/runtime exception in override resolution returns `None` (hard fallback to baseline).
- no startup/import crash path introduced by doctor config issues.

## 4. Supported live actions

Live now:
- `template_override_key`

Not live in this pass (intentionally ignored even if present in valid config):
- `route_label_override_key`

Other families not live:
- shade overrides
- routing overrides
- argen modes
- template override mappings
- material/manual-review/naming/scanner config

## 5. Fallback behavior

Baseline behavior is preserved when:
- doctor override file is missing,
- doctor override file is malformed,
- doctor override file is invalid,
- doctor override file is valid but no enabled rule matches,
- rule action lacks `template_override_key` (e.g., route-label-only action).

Fallback design details:
- loader applies per-family defaults on file read/validation failure.
- runtime override resolver is fail-safe (`except Exception -> None`).
- template selector always has baseline template output path as default path.

## 6. Validation performed

1. **Compile/import checks**
- Compiled:
  - `business_rule_loader.py`
  - `doctor_override_runtime.py`
  - `template_selector.py`
- Import smoke passed for:
  - `case_processor_final_clean`
  - `select_template_path`
  - `resolve_doctor_template_override_key`

2. **Focused live-behavior scenarios**
- no doctor config file -> baseline unchanged.
- malformed doctor config -> baseline unchanged.
- invalid doctor config schema -> baseline unchanged.
- valid doctor config, no matching doctor -> baseline unchanged.
- valid matching Abby/Dew-style doctor rule -> template override applied.
- valid matching Brier Creek-style doctor rule -> template override applied.
- valid config with unsupported live action only (`route_label_override_key`) -> ignored safely; baseline unchanged.

All checks passed.

## 7. Risks or limitations

- Doctor override preview is cached (`lru_cache`) for runtime stability/performance; edits to config files require process restart or explicit cache clear to reflect immediately.
- `route_label_override_key` is validated but intentionally non-live in this pass.
- Live behavior currently uses simple contains_any/contains_all substring matching semantics from the validated schema.
- Full production fixture replay was not executed; targeted scenario checks were run.

## 8. Recommended next pass

Safest next pass:

1. Keep doctor overrides live as-is.
2. Add optional non-disruptive diagnostics/status exposure for business-rule config load state (read-only visibility in existing UI/admin surfaces if desired).
3. Then enable one additional family live (recommended: **shade overrides** in narrow mode), with the same guardrails:
   - strict validation,
   - per-family fallback defaults,
   - no behavior change when missing/invalid/non-matching.

