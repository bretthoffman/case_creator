CASE CREATOR ARGEN MODES LIVE PASS REPORT

## 1. Summary of changes

This pass made **argen_modes config** live in a constrained, bounded way:
- live source: validated `argen_modes.json` via existing loader foundation.
- live effect: `contact_model_mode` only.
- supported mode values:
  - `legacy_default`
  - `always_with_contact_models`
  - `always_without_contact_models`

Live behavior is applied only at the narrow Argen modeless fast-path seam used by template selection logic.

## 2. Files modified

Created:
- `infrastructure/config/argen_modes_runtime.py`
- `CASE_CREATOR_ARGEN_MODES_LIVE_PASS_REPORT.md`

Modified:
- `infrastructure/config/business_rule_schemas.py`
- `infrastructure/config/business_rule_loader.py`
- `domain/rules/template_rules.py`
- `template_utils.py`

## 3. Live integration point

### Loader/validation
- `business_rule_schemas.py` now supports `argen_modes.json`:
  - file recognition,
  - default payload,
  - strict validation for `contact_model_mode` values only.
- `business_rule_loader.py` now includes `argen_modes` in effective config preview data.

### Runtime resolution
- `infrastructure/config/argen_modes_runtime.py` provides:
  - `resolve_contact_model_mode()` (fail-safe, cached),
  - `BASELINE_CONTACT_MODEL_MODE = "legacy_default"`.

### Application seam
- `domain/rules/template_rules.py` adds `effective_argen_hint_route(hint_route, material)`:
  - `legacy_default`: existing behavior unchanged.
  - `always_with_contact_models`: force Argen route family to `modeless`.
  - `always_without_contact_models`: force `modeless` route into non-modeless Argen family (`argen_adzir`/`argen_envision` by material).
- `template_utils.select_template(...)` now uses this effective hint route before existing branch engine evaluation.

This keeps branch order/engine ownership intact while applying the narrow mode influence.

## 4. Supported live behavior

Live now:
- `argen_modes.contact_model_mode` (strict enum).

Not live in this pass:
- zip behavior override config,
- label override config,
- raw path/template path override config,
- broad modeless policy DSL beyond the three supported modes.

Previously live and still active:
- doctor template override key,
- shade non-Argen marker override,
- routing family -> destination key override.

## 5. Fallback behavior

Baseline behavior is preserved when:
- `argen_modes.json` is missing,
- `argen_modes.json` is malformed,
- `argen_modes.json` is invalid,
- `contact_model_mode` is unsupported,
- mode is `legacy_default`.

Fail-safe behavior:
- loader keeps defaults on file/validation failure,
- runtime resolver catches exceptions and returns baseline mode,
- no startup/import crash path introduced.

## 6. Validation performed

1. **Compile/import checks**
- Compiled:
  - `business_rule_schemas.py`
  - `business_rule_loader.py`
  - `argen_modes_runtime.py`
  - `template_rules.py`
  - `template_utils.py`
- Import smoke passed for:
  - `case_processor_final_clean`
  - argen mode resolver and selector paths.

2. **Argen mode scenarios**
- no `argen_modes.json` -> baseline template behavior.
- malformed `argen_modes.json` -> baseline behavior.
- invalid `argen_modes.json` -> baseline behavior.
- valid baseline-equivalent config (`legacy_default`) -> unchanged behavior.
- valid `always_with_contact_models` -> constrained modeless-contact behavior engaged.
- valid `always_without_contact_models` -> constrained non-modeless behavior engaged.

3. **Cross-family regression checks**
- doctor override still applies as before.
- shade marker override still applies as before.
- routing override still applies as before.
- route labels remain baseline.

All checks passed.

## 7. Risks or limitations

- Mode resolver uses caching (`lru_cache`), so file edits require restart (or explicit cache clear) to apply immediately.
- The `always_without_contact_models` mapping from `modeless` to non-modeless uses material-based default family conversion; this is intentionally narrow but still a meaningful behavior pivot and should be monitored.
- Full production fixture replay was not executed; targeted scenario checks were used.

## 8. Recommended next pass

Safest next pass:

1. Keep current live families stable (doctor + shade + routing + argen_modes).
2. Add low-risk diagnostics/status exposure of effective config state in existing operational surfaces.
3. If another family is enabled next, use a similarly narrow scope (recommended: constrained `template_overrides` with strict known-key validation and explicit precedence boundaries), plus parity checks ensuring no baseline drift when absent/invalid.

