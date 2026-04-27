CASE CREATOR SHADE OVERRIDE LIVE PASS REPORT

## 1. Summary of changes

This pass made **shade override config** live in the narrowest supported way:
- live source: validated `shade_overrides.json` via existing business-rule loader.
- live effect: `non_argen_shade_markers` only.
- live integration seam: centralized non-Argen shade predicate in `domain/rules/template_rules.py`.

No other shade override behavior is live in this pass.

## 2. Files modified

Created:
- `infrastructure/config/shade_override_runtime.py`
- `CASE_CREATOR_SHADE_OVERRIDE_LIVE_PASS_REPORT.md`

Modified:
- `domain/rules/template_rules.py`

## 3. Live integration point

Runtime flow in this pass:

1. `template_rules.is_non_argen_shade(shade)` is the live predicate path used by `template_utils.select_template(...)`.
2. It now calls `resolve_non_argen_shade_markers(...)` from `infrastructure/config/shade_override_runtime.py`.
3. That helper reads validated effective shade config from `load_business_rule_config_preview()`.
4. If valid marker list exists and `shade_overrides.enabled` is true, those markers are used.
5. Otherwise, baseline markers (`C3`, `A4`) are used.

Safety design:
- hard fail-safe fallback to defaults on any exception.
- no startup/import crash path introduced by shade config issues.

## 4. Supported live behavior

Live now:
- `shade_overrides.non_argen_shade_markers` affects non-Argen shade classification.

Not live in this pass:
- `shade_overrides.rules` action engine (still non-live)
- shade conversion map overrides
- arbitrary shade template DSL
- raw template/path actions

Still non-live families:
- routing overrides
- argen modes
- template override mappings
- material/manual-review/naming/scanner config families

## 5. Fallback behavior

Baseline behavior is preserved when:
- shade override file is missing,
- shade override file is malformed,
- shade override file is invalid,
- shade override file is valid but marker set is equivalent to baseline,
- shade override family is disabled.

Fallback details:
- loader retains defaults per-family on read/validation failure.
- shade runtime resolver falls back to passed default markers for any runtime issue.
- no unrelated runtime behavior changes when no effective marker change applies.

## 6. Validation performed

1. **Compile/import checks**
- Compiled:
  - `infrastructure/config/shade_override_runtime.py`
  - `domain/rules/template_rules.py`
  - `template_utils.py`
  - `domain/decisions/template_selector.py`
- Import smoke passed for:
  - `case_processor_final_clean`
  - `resolve_non_argen_shade_markers`
  - `template_utils.is_non_argen_shade`

2. **Focused shade live behavior scenarios**
- no shade config file -> baseline classification unchanged.
- malformed shade config -> baseline classification unchanged.
- invalid shade config schema -> baseline classification unchanged.
- valid shade config reproducing baseline markers -> unchanged classification.
- valid shade config changing marker set (`A2` only) -> classification changed only as expected for non-Argen predicate.
- baseline template output unchanged when no effective marker change applies.

All checks passed.

3. **Non-live family guard check**
- Added routing override config file with a conflicting value.
- Confirmed destination selector output remained baseline (routing config still non-live).

## 7. Risks or limitations

- Shade runtime preview is cached (`lru_cache`) and requires process restart (or explicit cache clear) to pick up file edits immediately.
- Only marker-set override is live; shade rules list remains validated but non-live.
- Full production fixture replay was not executed; targeted scenario checks were performed.

## 8. Recommended next pass

Safest next pass:

1. Keep doctor + shade live as-is.
2. Add low-risk diagnostics/status exposure for business-rule load state (existing UI/admin surfaces if desired).
3. Then enable one additional family live in narrow mode (recommended: routing overrides by destination key), with strict per-family fallback and parity checks proving unchanged behavior when absent/invalid/non-matching.

