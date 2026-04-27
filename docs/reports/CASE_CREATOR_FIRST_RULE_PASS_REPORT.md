CASE CREATOR FIRST RULE PASS REPORT

## 1. Summary of changes

Implemented the first narrow, behavior-preserving rule-centralization pass by:
- creating the initial centralized rule/decision module structure,
- moving only low-risk pure helpers/constants,
- keeping legacy call sites behavior-compatible via thin wrappers/import indirection.

Created modules:
- `domain/rules/rule_models.py`
- `domain/rules/shade_rules.py`
- `domain/rules/doctor_rules.py`
- `domain/rules/material_rules.py`
- `domain/decisions/manual_review_selector.py`

Also created package markers:
- `domain/__init__.py`
- `domain/rules/__init__.py`
- `domain/decisions/__init__.py`

Updated legacy files to consume centralized helpers:
- `evo_to_case_data.py` now routes shade/material primitives through `domain.rules.*` while preserving existing helper names/call order.
- `template_utils.py` now imports doctor predicates from `domain.rules.doctor_rules`.

## 2. Files modified

Created:
- `domain/__init__.py`
- `domain/rules/__init__.py`
- `domain/decisions/__init__.py`
- `domain/rules/shade_rules.py`
- `domain/rules/doctor_rules.py`
- `domain/rules/material_rules.py`
- `domain/rules/rule_models.py`
- `domain/decisions/manual_review_selector.py`
- `CASE_CREATOR_FIRST_RULE_PASS_REPORT.md`

Modified:
- `evo_to_case_data.py`
- `template_utils.py`

## 3. Logic moved

### From `evo_to_case_data.py` -> `domain/rules/shade_rules.py`
- Shade conversion constants
- Shade order/rank constants
- Shade tokenization and normalization helpers
- Vita prefix stripping and canonicalization helpers
- Conversion helper
- Priority selection helper
- Final single-shade selection helper

### From `template_utils.py` -> `domain/rules/doctor_rules.py`
- `is_abby_dew`
- `is_vd_brier_creek`
- `is_signature_doctor` contract/implementation (same matching behavior)

### From `evo_to_case_data.py` -> `domain/rules/material_rules.py`
- Route extraction helper from service descriptions
- Material extraction helper from service descriptions
- Modeless detection helper
- Needs-model helper
- Related keyword constants for route/material extraction

### New decision contract module
- `domain/decisions/manual_review_selector.py` added with a minimal `ManualReviewDecision` usage path (`no_manual_review`) for future centralization.

### New shared model module
- `domain/rules/rule_models.py` added with minimal dataclasses:
  - `MaterialRouteHints`
  - `ManualReviewDecision`

## 4. Compatibility strategy

- Preserved existing helper names in `evo_to_case_data.py` (`_pick_single_shade`, `_route_from_services`, etc.) as wrappers that delegate to new modules.
- Preserved existing call order and behavior in `build_case_data_from_evo`.
- Kept `DISABLE_MODELESS` toggle semantics in `evo_to_case_data.py` exactly as before.
- Preserved `template_utils` public function names by importing the doctor predicates directly with same names.
- Did not move template precedence engine, destination routing, scanner mechanics, naming/suffix logic, or manual-review gate execution yet.

## 5. Validation performed

1. **Syntax/import validation**
- Ran `python3 -m compileall "evo_to_case_data.py" "template_utils.py" "domain"`
- Result: success, all updated/new modules compiled.

2. **Focused parity checks (runtime assertions)**
- Verified shade normalization outcomes:
  - `"Vita Classic-4M1, Vita Classic-4R1.5"` -> `"D3"`
  - `"bl2"` -> `"OM2"`
- Verified shade exception predicate behavior (`C3` true, `A2` false).
- Verified doctor predicates:
  - Abby/Dew matching true/false cases.
  - Brier Creek predicate true/false cases.
- Verified material/route helper outcomes:
  - Envision/modeless/model detection case.
  - ArgenZ/adz detection case.
- Result: all assertions passed.

3. **Circular import risk check**
- No circular import errors surfaced during compile/import/parity checks.

## 6. Risks or limitations

- Manual-review gate logic has not been migrated yet; only decision contract scaffolding was added.
- Template precedence logic remains in `template_utils.select_template` (intentionally not moved in this pass).
- Destination routing and scanner behavior remain in legacy processor (intentional for safety).
- `is_signature_doctor` still depends on runtime Excel path and `openpyxl` availability as before.
- Full end-to-end behavioral parity across all production case variants was not exhaustively replayed in this pass (only focused helper parity checks were run).

## 7. Recommended next pass

Safest next pass:
1. Introduce `domain/rules/manual_review_rules.py` with pure gate predicates/constants copied from processor.
2. Expand `domain/decisions/manual_review_selector.py` to evaluate manual-review gates in the exact current order.
3. Keep processor gate call sites intact by delegating to selector via compatibility wrapper, preserving current messages and return behavior.
4. Add focused parity checks for:
   - multi-unit gate outcomes,
   - unsupported-material gate outcomes,
   - Jotform manual-route outcomes.

This continues centralization while avoiding high-risk areas (template precedence, destination mapping, scanner mechanics).

