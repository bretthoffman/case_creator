CASE CREATOR SEVENTH RULE PASS REPORT

## 1. Summary of changes

This pass centralized pure template constants/predicates/helpers into a new template rules module while keeping `template_utils.select_template(...)` as the authoritative branch engine.

Changes made:
- Created `domain/rules/template_rules.py`.
- Centralized pure template helper logic:
  - `is_non_argen_shade(...)`
  - `is_itero_scanner(...)`
  - `is_adz_material(...)`
  - `normalized_hint_route(...)`
  - `build_template_path(...)`
  - `NON_ARGEN_SHADE_MARKERS` constant
- Updated `template_utils.py` to delegate to these helpers with minimal edits.
- Preserved the exact existing `if/elif` branch order and branch outcomes in `select_template(...)`.

## 2. Files modified

Created:
- `domain/rules/template_rules.py`
- `CASE_CREATOR_SEVENTH_RULE_PASS_REPORT.md`

Modified:
- `template_utils.py`

## 3. Logic moved

### Old location: `template_utils.py`
- Inline non-Argen shade predicate logic.
- Inline scanner-type check (`"itero" in scanner.lower()`).
- Repeated inline material-type checks (`"adz" in material` and negations).
- Inline material-hint route normalization (`material_hint.route` lowercasing).
- Inline template path assembly (`os.path.join(TEMPLATE_DIR, folder, f"{folder}.xml")`).

### New location: `domain/rules/template_rules.py`
- `is_non_argen_shade(shade)`
- `is_itero_scanner(scanner)`
- `is_adz_material(material)`
- `normalized_hint_route(case_data)`
- `build_template_path(folder)`
- `NON_ARGEN_SHADE_MARKERS`

### What did not move
- The branch engine and precedence order in `template_utils.select_template(...)`.
- Template decision ownership remains in `template_utils.select_template(...)`.

## 4. Compatibility strategy

- Kept `template_utils.select_template(...)` authoritative and unchanged in order/structure.
- Replaced only inline pure expressions with helper calls.
- Maintained all existing branch conditions semantically (including awkward/redundant branches).
- Kept returned folder names and template paths unchanged by delegating path assembly to `build_template_path(...)` with same path composition semantics.
- Kept downstream flow unchanged:
  - `domain/decisions/template_selector.py` still delegates to `template_utils.select_template(...)`,
  - processor and downstream consumers receive identical template paths.

## 5. Validation performed

1. **Compile checks**
- Ran:
  - `python3 -m compileall domain/rules/template_rules.py template_utils.py domain/decisions/template_selector.py case_processor_final_clean.py`
- Result: passed.

2. **Import/circular checks**
- Imported:
  - `template_utils`
  - `domain.rules.template_rules`
  - `domain.decisions.template_selector.select_template_path`
- Result: passed; no circular import issues observed.

3. **Focused representative branch checks**
- Verified template output outcomes for:
  - anterior branch
  - study vs non-study
  - signature vs non-signature
  - Abby/Dew case
  - Brier Creek-related case
  - non-Argen shade exception case
  - iTero vs non-iTero branch
  - modeless hint branch
- Result: all checks passed with expected template path suffixes.

## 6. Risks or limitations

- Full production fixture replay was not executed in this pass; validation was focused on representative template branches.
- Branch ownership is still in `template_utils.select_template(...)` by design; future passes must preserve exact order if ownership changes.
- `template_rules.build_template_path(...)` now owns template path assembly helper semantics; future changes there could affect all template outputs if not guarded by parity checks.

## 7. Recommended next pass

Safest next pass:

1. Introduce a light template decision result model (optional) and enrich `domain/decisions/template_selector.py` to return structured metadata while still delegating to authoritative `template_utils.select_template(...)`.
2. Keep processor using template path outputs exactly as-is.
3. Expand parity checks to include a larger matrix of route/material/signature/shade/scanner combinations to strengthen confidence before any future precedence ownership move.

This keeps risk low while preparing for a future controlled migration of precedence ownership.

